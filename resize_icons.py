import os
from PIL import Image

# 定义源目录和目标目录
source_dirs = [
    "res",
    "plugins/pi/res"
]

# 获取当前脚本所在目录作为基准目录
base_dir = os.path.dirname(os.path.abspath(__file__))

def resize_icons():
    for source_dir in source_dirs:
        # 构建完整的源目录路径和目标目录路径
        full_source_dir = os.path.join(base_dir, source_dir)
        
        # 遍历源目录中的所有文件
        for filename in os.listdir(full_source_dir):
            # 只处理.png文件且不以_disabled_开头且不以48.png结尾且不以_2x.png结尾
            if (filename.endswith(".png") and 
                not filename.startswith("_disabled_") and 
                not filename.endswith("48.png") and 
                not filename.endswith("_2x.png")):
                
                # 构建完整的文件路径
                source_path = os.path.join(full_source_dir, filename)
                
                # 构建目标文件路径
                name_without_ext = os.path.splitext(filename)[0]
                target_filename = f"{name_without_ext}_2x.png"
                target_path = os.path.join(full_source_dir, target_filename)
                
                # 如果目标文件已存在，则跳过
                if os.path.exists(target_path):
                    print(f"跳过 {target_path} (文件已存在)")
                    continue
                
                # 打开图像并调整大小
                try:
                    with Image.open(source_path) as img:
                        # 获取原始尺寸
                        width, height = img.size
                        
                        # 计算新的尺寸（2倍大小）
                        new_width = width * 2
                        new_height = height * 2
                        
                        # 调整图像大小
                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                        
                        # 保存调整大小后的图像
                        resized_img.save(target_path)
                        
                        print(f"已创建 {target_path} ({width}x{height} -> {new_width}x{new_height})")
                except Exception as e:
                    print(f"处理 {source_path} 时出错: {e}")

if __name__ == "__main__":
    resize_icons()