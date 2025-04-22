_base_ = 'rtmdet_tiny_8xb32-300e_coco.py'

# Model and training parameters
max_epochs = 100
batch_size = 32

# Dataset settings
data_root = 'data/'
metainfo = {
    'classes': ('fire', 'smoke'),
    'palette': [(220, 20, 60), (119, 11, 32)]
}

model = dict(
    bbox_head=dict(num_classes=2))

train_dataloader = dict(
    batch_size=batch_size,
    num_workers=4,
    dataset=dict(
        type='CocoDataset',
        data_root=data_root,
        ann_file='annotations/instances_train.json',
        data_prefix=dict(img='train/'),
        metainfo=metainfo
    )
)

val_dataloader = dict(
    batch_size=batch_size,
    num_workers=4,
    dataset=dict(
        type='CocoDataset',
        data_root=data_root,
        ann_file='annotations/instances_val.json',
        data_prefix=dict(img='val/'),
        metainfo=metainfo
    )
)

test_dataloader = val_dataloader

# Training settings
train_cfg = dict(
    type='EpochBasedTrainLoop',
    max_epochs=max_epochs,
    val_interval=10
)

test_evaluator = dict(
    ann_file='data/annotations/instances_test.json',
    backend_args=None,
    format_only=False,
    metric='bbox'
)

val_evaluator = dict(
    ann_file='data/annotations/instances_val.json',
    backend_args=None,
    format_only=False,
    metric='bbox'
)

# Use the pre-trained model
load_from = 'https://download.openmmlab.com/mmdetection/v3.0/rtmdet/rtmdet_tiny_8xb32-300e_coco/rtmdet_tiny_8xb32-300e_coco_20220902_112414-78e30dcc.pth'