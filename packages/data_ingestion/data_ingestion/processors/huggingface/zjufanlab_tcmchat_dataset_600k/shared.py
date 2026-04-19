"""存放药典文件处理链路共享的常量和路由键。"""

from data_ingestion.routing import FileRouteKey


DATASET_NAME = "ZJUFanLab/TCMChat-dataset-600k"
PHARMACOPOEIA_2022_FILE_PATH = "pretrain/train/books/national_standard/2022年中药药典.txt"

PHARMACOPOEIA_2022_ROUTE_KEY = FileRouteKey(
    provider="huggingface",
    dataset=DATASET_NAME,
    file_path=PHARMACOPOEIA_2022_FILE_PATH,
)
