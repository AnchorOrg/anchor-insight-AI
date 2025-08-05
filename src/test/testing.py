# please 
import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import subprocess
# TODO: english
# 导入get_focus_score模块
from src.app.get_focus_score import load_image_bytes, image_to_b64, get_focus_score

TEST_IMAGES_FOLDER = r"C:\Users\Administrator\Desktop\test_imgs"  # 测试图片文件夹路径
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']  # 支持的图片格式

def get_git_commit_hash():
    """获取当前git commit hash"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()[:8]  # 返回前8位
    except:
        # 如果没有git或不在git仓库中，返回当前时间戳的hash
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def load_image_from_path(image_path):
    """从指定路径加载图片"""
    with open(image_path, "rb") as f:
        return f.read()

def get_all_images(folder_path):
    """获取文件夹下所有支持格式的图片文件"""
    images = []
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"错误：文件夹 {folder_path} 不存在")
        return images
    
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            images.append(file_path)
    
    return sorted(images)  # 按文件名排序

def run_single_test(image_path, test_no):
    """对单张图片运行测试"""
    test_result = {
        "Test case No": test_no,
        "Title": "Get Focus Score",
        "Steps": "One-shoot",
        "Expectation (optional)": "Score",
        "Test result": "Failed",
        "Evidence commit hash": get_git_commit_hash(),
        "Image file": image_path.name
    }
    
    try:
        print(f"\n正在测试图片 {test_no}: {image_path.name}")

        img_bytes = load_image_from_path(image_path)
        img_b64 = image_to_b64(img_bytes)
        
        # 获取专注度分数
        score = get_focus_score(img_b64)
        if score >= 0:
            test_result["Test result"] = f"{score}"
            print(f"获得专注度分数: {score}")
        else:
            test_result["Test result"] = "Failed (Invalid score)"
            print("获取分数失败")
    except Exception as e:
        test_result["Test result"] = f"Failed ({type(e).__name__})"
        print(f"测试出错: {e}")
    return test_result

def main():
    """主测试函数"""
    print("="*60)
    print("开始测试 get_focus_score.py")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试图片文件夹: {TEST_IMAGES_FOLDER}")
    print("="*60)
    
    # 获取所有测试图片
    images = get_all_images(TEST_IMAGES_FOLDER)
    
    if not images:
        print(f"\n错误：在 {TEST_IMAGES_FOLDER} 中没有找到任何图片文件")
        print(f"支持的格式: {', '.join(SUPPORTED_FORMATS)}")
        return
    
    print(f"\n找到 {len(images)} 张测试图片")
    
    # 运行测试
    test_results = []
    
    for idx, image_path in enumerate(images, 1):
        result = run_single_test(image_path, idx)
        test_results.append(result)
        
        # 添加短暂延迟，避免API调用过快
        if idx < len(images):
            time.sleep(1)
    
    # 打印测试结果表格
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60 + "\n")
    
    # 准备表格数据（不包含图片文件名列）
    table_data = []
    for result in test_results:
        row = [
            result["Test case No"],
            result["Title"],
            result["Steps"],
            result["Expectation (optional)"],
            result["Test result"],
            result["Evidence commit hash"]
        ]
        table_data.append(row)
    
    # 表格头
    headers = [
        "Test case No",
        "Title",
        "Steps",
        "Expectation (optional)",
        "Test result",
        "Evidence commit hash"
    ]
    
    # 打印表格
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # 打印测试统计
    print("\n" + "="*60)
    print("测试统计")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["Test result"].isdigit())
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
    
    # 打印分数分布（如果有）
    scores = [int(r["Test result"]) for r in test_results if r["Test result"].isdigit()]
    if scores:
        print(f"\n专注度分数分布:")
        print(f"  最低分: {min(scores)}")
        print(f"  最高分: {max(scores)}")
        print(f"  平均分: {sum(scores)/len(scores):.1f}")
    
    # 保存详细结果到文件
    report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("Get Focus Score 测试报告\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Git Commit: {get_git_commit_hash()}\n\n")
        
        f.write("详细测试结果:\n")
        f.write(tabulate(table_data, headers=headers, tablefmt="grid"))
        f.write("\n\n测试文件列表:\n")
        
        for result in test_results:
            f.write(f"  Test {result['Test case No']}: {result['Image file']} -> Score: {result['Test result']}\n")
    
    print(f"\n详细测试报告已保存至: {report_filename}")
    print("\n测试完成!")

if __name__ == "__main__":
    # 创建测试图片文件夹（如果不存在）
    if not os.path.exists(TEST_IMAGES_FOLDER):
        os.makedirs(TEST_IMAGES_FOLDER)
        print(f"已创建测试文件夹: {TEST_IMAGES_FOLDER}")
        print("请将测试图片放入该文件夹后重新运行")
        sys.exit(0)
    main()
