python >= 3.8

## 数据格式：
出于方便和通用

## 注意
运行程序前须在根目录下建立 `output` 和 `log` 文件夹

在程序中以 `dict` 形式存储，输出为 `JSON` 字符串格式。
### 输出文件格式
 - 检索结果：`jsonl`

### 单条博文
```python
blog_item: {
    # 由数字和字母组成的博文唯一标识符（更为常用）
    mblogid: str = "MC0gRd2CF",
    # 由数字组成的博文唯一标识符
    mid: str = "4890575093108349",
    # 由数字组成的平台用户唯一标识符
    uid: str = "2656274875",
    # GMT 格式的发布时间字符串
    created_at: str = "Fri Apr 14 23:50:27 +0800 2023",
    # 博文发布时用户的 ip 地址
    region_name: str = "北京",
    # 客户端类型
    source: str = "HUAWEI P40 Pro 5G",
    # 编辑次数
    edit_count: int = 1,
    # 博文类型（还未知具体指什么）
    mblogtype: int = 0,
    # 博文 level（还未知具体指什么）
    mlevel: int = 145448,
    # 是否是长文本
    isLongText: int = 1,

    # 博文文本内容
    content: str = "【#习主席用三个关键词定位中巴关系#】今天，#习近平同巴西总统举行会谈#。关于中巴关系，习主席提到三个关键词：战略高度、长远角度、优先位置，给出了一个非常清晰的定位。两国分处地球东西两端，虽是远隔天涯，却建立起紧密的伙伴关系。欢迎仪式上还有一个动人的细节，军乐团特意演奏了一首巴西特色音乐《新时代》，相信以此访为契机，两国关系也将迎来新时代、开辟新未来。#主播说联播# http://t.cn/A6NthgM3",
    # 图片数量
    pic_num: int = 6,
    # 图片唯一标识符列表
    pic_ids: list[str] = [
        "002TLsr9ly1hd0dsvntxsj60u00nvndz02",
        "002TLsr9ly1hd0elq0zgej60i40aa75i02",
        "002TLsr9ly1hd0dsvw92fj60rs0ij76k02",
        "002TLsr9ly1hd0dsw37kmj60u00nntw702",
        "002TLsr9ly1hd0dswrhzvg60hs0afb2d02",
        "002TLsr9ly1hd0dswa19oj60to0gngyg02"
    ],

    # 转发数
    reposts_count: int = 32,
    # 评论数
    comments_count: int = 12,
    # 是否开启评论精选
    comment_selected: int = 1,
    # 点赞数
    attitudes_count: int = 98,

    # 爬取时刻时间戳
    ts: int = 1680918561
}
```
