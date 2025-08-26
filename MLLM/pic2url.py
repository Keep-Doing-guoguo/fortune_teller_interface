import oss2
import os
from config import accessKeyId_,accessKeySecret_

def pic2url(path):
    # 固定写死的 AccessKey ID 和 AccessKey Secret
    accessKeyId = accessKeyId_
    accessKeySecret = accessKeySecret_

    # 创建认证对象
    auth = oss2.Auth(accessKeyId, accessKeySecret)

    # Endpoint（北京）
    endpoint = "https://oss-cn-beijing.aliyuncs.com"

    # Bucket 名称
    bucketName = "my-image-bed-88"
    bucket = oss2.Bucket(auth, endpoint, bucketName)

    # Object 名称（OSS 路径）
    objectName = "test/" + os.path.basename(path)

    # 上传文件
    bucket.put_object_from_file(objectName, path)

    # 生成公网访问链接
    fileLink = f"https://{bucketName}.oss-cn-beijing.aliyuncs.com/{objectName}"
    print(fileLink)
    return fileLink


# if __name__ == "__main__":
#     pic2url("/Volumes/PSSD/未命名文件夹/fortune_teller-main/img/2.png")

#执行完毕后的结果为：
#https://my-image-bed-88.oss-cn-beijing.aliyuncs.com/test/2.png



