# SunoMusic 音乐生成插件

<!--
## 插件开发者详阅

### 开始

此仓库是 LangBot 插件模板，您可以直接在 GitHub 仓库中点击右上角的 "Use this template" 以创建你的插件。  
接下来按照以下步骤修改模板代码：

#### 修改模板代码

- 修改此文档顶部插件名称信息
- 将此文档下方的`<插件发布仓库地址>`改为你的插件在 GitHub· 上的地址
- 补充下方的`使用`章节内容
- 修改`main.py`中的`@register`中的插件 名称、描述、版本、作者 等信息
- 修改`main.py`中的`MyPlugin`类名为你的插件类名
- 将插件所需依赖库写到`requirements.txt`中
- 根据[插件开发教程](https://docs.langbot.app/plugin/dev/tutor.html)编写插件代码
- 删除 README.md 中的注释内容


#### 发布插件

推荐将插件上传到 GitHub 代码仓库，以便用户通过下方方式安装。   
欢迎[提issue](https://github.com/RockChinQ/LangBot/issues/new?assignees=&labels=%E7%8B%AC%E7%AB%8B%E6%8F%92%E4%BB%B6&projects=&template=submit-plugin.yml&title=%5BPlugin%5D%3A+%E8%AF%B7%E6%B1%82%E7%99%BB%E8%AE%B0%E6%96%B0%E6%8F%92%E4%BB%B6)，将您的插件提交到[插件列表](https://github.com/stars/RockChinQ/lists/qchatgpt-%E6%8F%92%E4%BB%B6)

下方是给用户看的内容，按需修改
-->
一个基于 Suno API 的音乐生成插件，支持自然语言描述生成音乐。

## 安装

配置完成 [LangBot](https://github.com/RockChinQ/LangBot) 主程序后使用管理员账号向机器人发送命令即可安装：

```
!plugin get https://github.com/sanxianxiaohuntun/SunoMusic.git
```
或查看详细的[插件安装说明](https://docs.langbot.app/plugin/plugin-intro.html#%E6%8F%92%E4%BB%B6%E7%94%A8%E6%B3%95)


## 功能特点

- 支持详细音乐描述生成
- 支持简单灵感模式生成
- 自动后台查询生成状态
- 支持手动查询生成进度
- 生成完成自动发送音乐和封面

## 命令列表

### 1. 生成音乐
/生成音乐 [音乐描述]<br>
例：<br>
/生成音乐 <br>
(Verse 1)
遇见你 那天阳光正好
微风轻轻 吹动你的发梢
你的笑容 像一朵花儿
在我心里 悄悄地开放了

(Chorus)
我爱你 简单又美好
像吉他 轻轻地弹唱
我爱你 不需要理由
只想和你 一起慢慢变老

(Verse 2)
我们一起 走过大街小巷
分享彼此 生活的点点滴滴
你的快乐 是我的快乐
你的忧伤 我也为你分担

(Chorus)
我爱你 简单又美好
像吉他 轻轻地弹唱
我爱你 不需要理由
只想和你 一起慢慢变老

(Bridge)
未来的路 还很长
让我们 手牵手一起闯
不怕风雨 不怕阻挡
有你在身边 就是我的天堂

(Chorus)
我爱你 简单又美好
像吉他 轻轻地弹唱
我爱你 不需要理由
只想和你 一起慢慢变老

(Outro)
我爱你 我爱你
这是我 心底的声音

风格三：浪漫R&B

(Intro)
Baby, you know...
It's all about you...

(Verse 1)
你的眼神 像迷人的漩涡
让我深陷 无法自拔
你的声音 像天籁般动听
让我沉醉 无法抗拒

(Pre-Chorus)
每一次呼吸 都是你的气息
每一次心跳 都是因为你

(Chorus)
我爱你 如此深刻 如此痴迷
你的每一个细节 都让我着迷
我爱你 无法言喻 无法代替
你是我生命中 最美的奇迹

(Verse 2)
你的温柔 融化了我的心
你的拥抱 给我无限的勇气
和你一起 每一天都充满甜蜜
这是我 最幸福的记忆

(Pre-Chorus)
每一次呼吸 都是你的气息
每一次心跳 都是因为你

(Chorus)
我爱你 如此深刻 如此痴迷
你的每一个细节 都让我着迷
我爱你 无法言喻 无法代替
你是我生命中 最美的奇迹

(Bridge)
Baby, I wanna spend my life with you
Forever and ever, this love is true

(Chorus)
我爱你 如此深刻 如此痴迷
你的每一个细节 都让我着迷
我爱你 无法言喻 无法代替
你是我生命中 最美的奇迹

(Outro)
I love you, baby
You are my everything...

### 2. 简单生成音乐
/简单生成音乐 [简单描述]
示例：
/简单生成音乐 一首轻快的流行音乐，带有钢琴伴奏

### 3. 查询状态
/音乐状态 [任务ID
示例：
/音乐状态 ba3a7d9b-fbd7-3c70-303a-0d2d8d66c50d

## 使用流程

1. 使用 `/生成音乐` 或 `/简单生成音乐` 提交生成任务
2. 系统会返回任务ID并开始后台生成
3. 生成过程中可以使用 `/音乐状态` 查询进度
4. 生成完成后会自动发送：
   - 音乐标题和描述
   - 封面图片
   - 音频文件
   - 保存信息

## 注意事项

- 每个任务会生成两首不同风格的音乐
- 生成过程可能需要几分钟时间
- 系统会每30秒自动查询一次生成状态
- 生成的音乐文件会保存在插件目录下的 music 文件夹中

## 安装说明

1. 将插件文件夹放入 plugins 目录
2. 在 config.yaml 中配置以下信息：
   - api_base: API基础地址
   - api_token: API访问令牌
   - model: 使用的模型名称

![01a0d883536bf1a85c46c11e4991c306](https://github.com/user-attachments/assets/b4ab836b-1920-4b8f-a5c4-1670a5753d33)


<!-- 插件开发者自行填写插件使用说明 -->
