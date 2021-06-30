# Build_Change_Detection
Change Detection, Tensorflow2，
  
  
# 项目介绍  
本项目为研究性质，其主要目的是检测多时相遥感影像中建筑物发生变化的区域检测，其变化包括新增与消失。  
  
# 运行环境  
tensorflow2.0+, numpy 1.18.1, opencv-python 4.5.1.48  
  
# 检测效果  
从左至右依次是  
原始图像1 -> 原始图像2 —> 不用管 -> 不用管 -> 检测结果图 -> 真实标签图  
![image](./detection_images/94.png)  

![image](./detection_images/104.png)  

# 文件夹介绍  
1、detection_images      :       检测结果存放路径  
2、model                 :       5个神经网络模型  
3、train                 :       模型训练  
4、detection.py          :       预测模块  

# 作者  
长沙理工大学1103实验室  
  
# 未完待续  