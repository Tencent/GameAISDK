# Task识别结果说明

[TOC]

## 1 识别结果参数介绍

| 参数名           | 参数解释                                |
| ---------------- | --------------------------------------- |
| groupID          | 组ID号                                  |
| frmeSeq          | 针序号                                  |
| image            | 图像数据                                |
| deviceIndex      | 设备ID                                  |
| taskId           | Task的Id编号                            |
| flag             | 当前识别结果的可用标识，true            |
| ROI              | 检测区域，x,y,w,h表示识别区域           |
| boxs             | 识别结果列表                            |
| tmplName         | 匹配的模板名                            |
| score            | 匹配分值                                |
| scale            | 匹配尺度                                |
| points           | 识别到的点的位置，x,y为点的坐标         |
| percent          | 识别百分比                              |
| level            | King Glory Blood下的Level表示英雄的级别 |
| classID          | 模板类型Id号                            |
| num              | 识别到的数字                            |
| viewAnglePoint   | 视觉角度，x,y表示视觉的角度             |
| myLocPoint       | 自己的位置点，x,y表示自己位置的坐标     |
| friendsLocPoints | 友方位置点，x,y表示友方的位置的坐标     |
| ViewLocPoint     | 视觉点，x,y表示视觉点的坐标             |
| colorMeanVar     | 受伤检测颜色均值，值越小表示检测到受伤  |



## 2 各算法返回结果

### 2.1Fix Object 任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'ROI': {
                    'x': int,
                    'y': int,
                    'w': int,
                    'h': int
                },
                'boxes': [
                    {
                        'tmplName': str,
                        'score': float,
                        'scale': float,
                        'classID': int,
                        'x': int,
                        'y': int,
                        'w': int,
                        'h': int
                    }
                ]
            }
        ]
    }
}



### 2.2 Pixel任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'points': [
                    {
                        'x': int,
                        'y': int
                    }
                ]
            }
        ]
    }
}

### 2.3  Stuck任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'x': int,
                'y': int,
                'w': int,
                'h': int
            }
        ]
    }
}

### 2.4 Deform object任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'boxes': [
                    {
                        'tmplName': str,
                        'score': float,
                        'scale': float,
                        'classID': int,
                        'x': int,
                        'y': int,
                        'w': int,
                        'h': int
                    }
                ]
            }
        ]
    }
}

### 2.5 Number任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'num': float,
                'x': int,
                'y': int,
                'w': int,
                'h': int
            }
        ]
    }
}

### 2.6 Fix Blood任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'percent': float,
                'ROI': {
                    'x': int,
                    'y': int,
                    'w': int,
                    'h': int
                },
                'box': {
                    'x': int,
                    'y': int,
                    'w': int,
                    'h': int
                }
            }
        ]
    }
}

### 2.7 King Glory Blood任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'ROI': {
                    'x': int,
                    'y': int,
                    'w': int,
                    'h': int
                },
                'bloods': [
                    {
                        'classID': int,
                        'level': int,
                        'score': float,
                        'percent': float,
                        'name': str,
                        'x': int,
                        'y': int,
                        'w': int,
                        'h': int
                    }
                ]
            }
        ]
    }
}

### 2.8 map 任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'viewAnglePoint': {
                    'y': int,
                    'x': int
                },
                'ROI': {
                    'y': int,
                    'w': int,
                    'x': int,
                    'h': int
                },
                'flag': bool,
                'myLocPoint': {
                    'y': int,
                    'x': int
                },
                'friendsLocPoints': [
                    {
                        'y': int,
                        'x': int
                    }
                ]
            }
        ]
    }
}

### 2.9 mapDirection任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'flag': bool,
                'ROI': {
                    'x': int,
                    'y': int,
                    'w': int,
                    'h': int
                },
                'ViewAnglePoint': {
                    'x': int,
                    'y': int,
                         
                }'ViewLocPoint': {
                           'x': int,
                           'y': int,
                                 
                }'MyLocPoint': {
                           'x': int,
                           'y': int,
                                 
                }   
            ] 
        }
    ]
}
}

###  2.10 multcolorvar 任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'colorMeanVar': [
                 float
                ],
                'flag': bool
            }
        ]
    }
}

### 2.11 shoot game blood任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'box': {
                    'w': int,
                    'h': int,
                    'x': int,
                    'y': int
                },
                'ROI': {
                    'w': int,
                    'h': int,
                    'x': int,
                    'y': int
                },
                'flag': bool,
                'percent': float
            }
        ]
    }
}

### 2.12 shoot game hurt 任务结果

{
    'groupID': int,
    'frameSeq': int,
    'image': mat,
    'deviceIndex': int,
    'result': {
        //taskID: result1: [
            {
                'ROI': {
                    'w': int,
                    'h': int,
                    'x': int,
                    'y': int
                },
                'flag': bool
            }
        ]
    }
}