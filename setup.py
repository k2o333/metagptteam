from setuptools import setup, find_packages

# 最好从一个 requirements.txt 文件读取依赖
# 为简化，这里直接写出
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="mghier",
    version="0.1.0",
    packages=find_packages(),
    install_requires=required  # <-- 关键补充
)