增加接入AI的方式
1, 给新AI商建一个目录
2，在该目录下创建立文件 __init__.py  里面写一行代码: from .queryAI import chatWithAI
3, 再在该目录下创建文件 queryAI.py, 里面创建实现函数 对接接口：
  chatWithAI(prompt, from_uid, model, key, config_json=None)
  该函数返回 {'ok': True, 'answer': "AI response data", 'desc': "descriptino"}
