import os
import json
import time
import aiohttp
import asyncio
import yaml
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.platform.types import Voice, Plain, Image
import base64
import requests


# 注册插件
@register(name="SunoMusic音乐生成", description="使用 Suno API 生成音乐", version="0.1", author="小馄饨")
class SunoPlugin(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        super().__init__(host)
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.api_base = config['api_base']
        self.auth_token = config['api_token']
        self.model = config['model']
        
        # 创建必要的目录
        self.plugin_dir = os.path.dirname(__file__)
        self.music_dir = os.path.join(self.plugin_dir, 'music')
        self.exe_dir = os.path.join(self.plugin_dir, 'exe')
        
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.exe_dir, exist_ok=True)
        
        # 检查转换工具是否存在
        self.ffmpeg_path = os.path.join(self.exe_dir, 'ffmpeg.exe')
        self.encoder_path = os.path.join(self.exe_dir, 'silk_v3_encoder.exe')
        
        if not os.path.exists(self.ffmpeg_path):
            print(f"[ERROR] ffmpeg.exe 不存在: {self.ffmpeg_path}")
        if not os.path.exists(self.encoder_path):
            print(f"[ERROR] silk_v3_encoder.exe 不存在: {self.encoder_path}")
        
        # 添加任务ID存储
        self.current_task_id = None

    # 异步初始化
    async def initialize(self):
        pass

    async def submit_music_task(self, prompt: str, is_inspiration: bool = False) -> dict:
        """提交音乐生成任务"""
        url = f"{self.api_base}/suno/submit/music"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model
        }
        
        if is_inspiration:
            data["gpt_description_prompt"] = prompt
        else:
            data["prompt"] = prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"[ERROR] API请求失败: HTTP {response.status}")
                        return {"error": f"HTTP {response.status}", "response": response_text}
                    
                    try:
                        result = json.loads(response_text)
                        if result.get("code") == "success":
                            return {
                                "task_id": result.get("data"),
                                "status": "success"
                            }
                        else:
                            print(f"[ERROR] API返回错误: {result}")
                            return {"error": "API返回错误", "response": result}
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON解析失败: {str(e)}")
                        return {"error": "JSON解析失败", "response": response_text}
                        
        except Exception as e:
            print(f"[ERROR] 请求异常: {str(e)}")
            return {"error": str(e)}

    async def check_task_status(self, task_id: str) -> dict:
        """检查任务状态"""
        url = f"{self.api_base}/suno/fetch/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"[ERROR] API请求失败: HTTP {response.status}")
                        return {"error": f"HTTP {response.status}", "response": response_text}
                    
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON解析失败: {str(e)}")
                        return {"error": "JSON解析失败", "response": response_text}
                        
        except Exception as e:
            print(f"[ERROR] 请求异常: {str(e)}")
            return {"error": str(e)}

    async def download_music(self, url: str, filename: str) -> str:
        """下载音乐文件"""
        file_path = os.path.join(self.music_dir, filename)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                    return file_path
                return None

    async def poll_task_status(self, task_id: str, max_attempts: int = 30) -> dict:
        """轮询任务状态"""
        attempts = 0
        while attempts < max_attempts:
            result = await self.check_task_status(task_id)
            status = result.get("status")
            
            if status == "succeeded":
                return result
            elif status == "failed":
                raise Exception("音乐生成失败")
            
            attempts += 1
            await asyncio.sleep(10)  # 每10秒检查一次
        
        raise Exception("生成超时")

    async def process_music_generation(self, ctx: EventContext, chat_type: str, target_id: str, prompt: str, is_inspiration: bool = False):
        """处理音乐生成的完整流程"""
        try:
            # 提交任务
            result = await self.submit_music_task(prompt, is_inspiration)
            
            # 检查是否有错误
            if "error" in result:
                await ctx.send_message(chat_type, target_id, [Plain(f"音乐生成任务提交失败: {result['error']}")])
                return
                
            task_id = result.get("task_id")
            if not task_id:
                await ctx.send_message(chat_type, target_id, [Plain("音乐生成任务提交失败: 未获取到任务ID")])
                return
            
            # 存储当前任务ID
            self.current_task_id = task_id
            
            # 分两次发送提示信息
            await ctx.send_message(chat_type, target_id, 
                [Plain("音乐生成任务已提交，稍后使用下方ID进行\"/音乐状态\"进行手动查询，我也会后台30秒自动查询一次请稍等。")])
            await ctx.send_message(chat_type, target_id, 
                [Plain(task_id)])
            
            # 后台轮询任务状态
            while True:
                status, progress, result = await self.get_task_progress(task_id)
                if status == "已完成" and result:
                    await self.handle_completed_music(ctx, chat_type, target_id, result)
                    break
                elif status.startswith("生成失败"):
                    await ctx.send_message(chat_type, target_id, [Plain(f"音乐生成失败: {status}")])
                    break
                    
                # 等待30秒后再次查询
                await asyncio.sleep(30)
            
        except Exception as e:
            await ctx.send_message(chat_type, target_id, [Plain(f"发生错误: {str(e)}")])

    def convert_to_silk(self, mp3_path: str, silk_path: str) -> bool:
        """将MP3转换为silk格式"""
        try:
            # 检查转换工具是否存在
            if not os.path.exists(self.ffmpeg_path):
                print(f"[ERROR] ffmpeg.exe 不存在: {self.ffmpeg_path}")
                return False
            if not os.path.exists(self.encoder_path):
                print(f"[ERROR] silk_v3_encoder.exe 不存在: {self.encoder_path}")
                return False
            
            # 检查源文件是否存在
            if not os.path.exists(mp3_path):
                print(f"[ERROR] 源文件不存在: {mp3_path}")
                return False
                
            # 使用绝对路径
            pcm_path = f"{mp3_path}.pcm"
            
            print(f"[DEBUG] 开始转换:")
            print(f"ffmpeg路径: {self.ffmpeg_path}")
            print(f"源文件: {mp3_path}")
            print(f"PCM文件: {pcm_path}")
            print(f"目标文件: {silk_path}")
            
            # 转换为PCM，使用绝对路径并用双引号包裹
            cmd1 = f'"{self.ffmpeg_path}" -y -i "{mp3_path}" -f s16le -ar 24000 -ac 1 "{pcm_path}"'
            print(f"执行命令: {cmd1}")
            
            # 切换到 exe 目录执行命令
            original_dir = os.getcwd()
            os.chdir(self.exe_dir)
            
            ret1 = os.system(f'ffmpeg.exe -y -i "{mp3_path}" -f s16le -ar 24000 -ac 1 "{pcm_path}"')
            if ret1 != 0:
                print(f"[ERROR] PCM转换失败: {ret1}")
                os.chdir(original_dir)
                return False
            
            # 转换为SILK
            ret2 = os.system(f'silk_v3_encoder.exe "{pcm_path}" "{silk_path}" -rate 24000 -tencent')
            if ret2 != 0:
                print(f"[ERROR] SILK转换失败: {ret2}")
                os.chdir(original_dir)
                return False
            
            # 切回原目录
            os.chdir(original_dir)
            
            # 清理临时文件
            if os.path.exists(pcm_path):
                os.remove(pcm_path)
            
            return os.path.exists(silk_path)
        except Exception as e:
            print(f"[ERROR] 转换失败: {str(e)}")
            # 确保切回原目录
            if 'original_dir' in locals():
                os.chdir(original_dir)
            return False

    async def get_task_progress(self, task_id: str) -> tuple[str, int, dict]:
        """获取任务进度"""
        try:
            result = await self.check_task_status(task_id)
            if result.get("code") != "success":
                return "查询失败", 0, None
                
            data = result.get("data", {})
            status = data.get("status", "").upper()  # API返回的是大写状态
            progress_str = data.get("progress", "0%")
            # 将进度百分比字符串转为数字
            progress = int(progress_str.strip('%')) if progress_str else 0
            
            if status == "SUCCESS":
                return "已完成", 100, result
            elif status == "FAILED":
                fail_reason = data.get("fail_reason", "未知原因")
                return f"生成失败: {fail_reason}", 0, None
            elif status == "PROCESSING":
                return "生成中", progress, None
            else:
                return "等待中", progress, None
                
        except Exception as e:
            print(f"[ERROR] 解析任务状态失败: {str(e)}")
            return f"查询失败: {str(e)}", 0, None

    async def handle_completed_music(self, ctx: EventContext, chat_type: str, target_id: str, result: dict):
        """处理已完成的音乐"""
        try:
            # 获取音乐文件URL
            data_list = result.get("data", {}).get("data", [])
            if not data_list:
                await ctx.send_message(chat_type, target_id, [Plain("未找到音乐文件")])
                return
                
            # 遍历所有音乐文件
            for index, music_data in enumerate(data_list, 1):
                music_url = music_data.get("audio_url")
                image_url = music_data.get("image_url")
                prompt = music_data.get("prompt", "")
                title = music_data.get("title", "无标题")
                duration = music_data.get("duration", 0)
                
                if not music_url:
                    await ctx.send_message(chat_type, target_id, [Plain(f"获取第{index}首音乐文件失败")])
                    continue
                
                # 下载音乐文件，使用任务ID和序号作为文件名
                task_id = music_data.get("task_id", "").split("_")[0]  # 移除任务ID中的后缀
                filename = f"{task_id}_{index}.mp3"  # 移除时间戳
                file_path = await self.download_music(music_url, filename)
                
                if not file_path:
                    await ctx.send_message(chat_type, target_id, [Plain(f"下载第{index}首音乐文件失败")])
                    continue
                
                # 发送标题和歌词
                await ctx.send_message(chat_type, target_id, [
                    Plain(f"🎵 {title}\n"),
                    Plain(f"📝 歌词/提示词：{prompt}")
                ])
                
                # 发送封面图片（单独发送）
                if image_url:
                    await ctx.send_message(chat_type, target_id, [Image(url=image_url)])
                
                # 发送文件信息
                await ctx.send_message(chat_type, target_id, [
                    Plain(f"💾 音乐文件已保存: {filename}")
                ])
                
                # 下载并发送音频文件（单独发送）
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(music_url) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                audio_base64 = base64.b64encode(audio_data).decode()
                                await ctx.send_message(chat_type, target_id, [Voice(base64=audio_base64)])
                except Exception as e:
                    print(f"[ERROR] 发送第{index}首音频失败: {str(e)}")
                    await ctx.send_message(chat_type, target_id, [Plain("音频发送失败，但文件已保存")])
                
                # 如果还有下一首歌，添加等待提示
                if index < len(data_list):
                    await ctx.send_message(chat_type, target_id, [
                        Plain(f"⏳ 请等待第{index+1}首音乐...")
                    ])
                
        except Exception as e:
            await ctx.send_message(chat_type, target_id, [Plain(f"处理音乐文件时发生错误: {str(e)}")])

    async def handle_status_command(self, ctx: EventContext, chat_type: str, target_id: str, task_id: str):
        """处理状态查询命令"""
        status, progress, result = await self.get_task_progress(task_id)
        
        # 构建状态消息
        message_parts = [
            Plain(f"🎵 任务ID: {task_id}\n"),
            Plain(f"⏳ 当前状态: {status}\n"),
            Plain(f"📊 完成进度: {progress}%")
        ]
        
        await ctx.send_message(chat_type, target_id, message_parts)
            
        # 如果任务完成，自动下载并发送
        if status == "已完成" and result:
            await ctx.send_message(chat_type, target_id, [Plain("\n🎉 音乐生成完成，正在处理文件...")])
            await self.handle_completed_music(ctx, chat_type, target_id, result)

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, ctx: EventContext):
        msg = ctx.event.text_message
        if msg.startswith("/生成音乐"):
            ctx.prevent_default()
            prompt = msg[5:].strip()
            
            if not prompt:
                await ctx.send_message("person", ctx.event.sender_id, 
                    [Plain("请提供音乐描述，例如：/生成音乐 一首轻快的流行音乐")])
                return
            
            await self.process_music_generation(ctx, "person", ctx.event.sender_id, prompt)
            
        elif msg.startswith("/简单生成音乐"):
            ctx.prevent_default()
            prompt = msg[7:].strip()
            
            if not prompt:
                await ctx.send_message("person", ctx.event.sender_id, 
                    [Plain("请提供简单描述，例如：/简单生成音乐 猫")])
                return
            
            # 使用灵感模式生成
            await self.process_music_generation(ctx, "person", ctx.event.sender_id, prompt, True)
        
        elif msg.startswith("/音乐状态"):
            ctx.prevent_default()
            parts = msg.split(maxsplit=1)
            task_id = parts[1].strip() if len(parts) > 1 else self.current_task_id
            
            if not task_id:
                await ctx.send_message("person", ctx.event.sender_id, 
                    [Plain("请提供任务ID或先生成音乐\n例如：/音乐状态 task-id-here")])
                return
                
            await self.handle_status_command(ctx, "person", ctx.event.sender_id, task_id)

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        msg = ctx.event.text_message
        if msg.startswith("/生成音乐"):
            ctx.prevent_default()
            prompt = msg[5:].strip()
            
            if not prompt:
                await ctx.send_message("group", ctx.event.launcher_id, 
                    [Plain("请提供音乐描述，例如：/生成音乐 一首轻快的流行音乐")])
                return
            
            await self.process_music_generation(ctx, "group", ctx.event.launcher_id, prompt)
            
        elif msg.startswith("/简单生成音乐"):
            ctx.prevent_default()
            user_prompt = msg[7:].strip()
            
            if not user_prompt:
                await ctx.send_message("group", ctx.event.launcher_id, 
                    [Plain("请提供简单描述，例如：/简单生成音乐 开心")])
                return
            
            # 构建简化的提示词
            prompt = f"[verse]A {user_prompt} song"
            await self.process_music_generation(ctx, "group", ctx.event.launcher_id, prompt)
            
        elif msg.startswith("/音乐状态"):
            ctx.prevent_default()
            parts = msg.split(maxsplit=1)
            task_id = parts[1].strip() if len(parts) > 1 else self.current_task_id
            
            if not task_id:
                await ctx.send_message("group", ctx.event.launcher_id, 
                    [Plain("请提供任务ID或先生成音乐\n例如：/音乐状态 task-id-here")])
                return
                
            await self.handle_status_command(ctx, "group", ctx.event.launcher_id, task_id)

    # 插件卸载时触发
    def __del__(self):
        pass
