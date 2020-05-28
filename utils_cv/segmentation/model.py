# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from pathlib import Path
from typing import Callable, List, Tuple, Union, Generator, Optional, Dict

#import fastai
from fastai.basic_data import DeviceDataLoader
from fastai.basic_train import Learner
#from fastai.vision import * 
import numpy as np
import PIL
from sklearn.metrics import confusion_matrix as sk_confusion_matrix

from .dataset import load_im


def predict(
    im_or_path: Union[np.ndarray, Union[str, Path]], 
    learn: Learner,
    thres: float = None
) -> [np.ndarray, np.ndarray]:
    """ Run model inference. 
      
    Args:
        im_or_path: image or path to image
        learn: trained model
        thres: threshold under which to reject predicted label and set to class-id 0 instead.

    Return:
        The predicted mask with confidence scores.
    """
    im = load_im(im_or_path)  # open_image(im_path, convert_mode='RGB')
    _, mask, scores = learn.predict(im, thresh=thres)
    mask = np.array(mask).squeeze()
    scores = np.array(scores)

    # Fastai seems to ignore the confidance threshold 'thresh'. Hence here
    # setting all predictions with low confidence to be 'background'.
    if thres is not None:
        max_scores = np.max(np.array(scores), axis=0)
        mask[max_scores <= thres] = 0

    return mask, scores


def confusion_matrix(
    learn: Learner,
    dl: DeviceDataLoader, 
    thres: float = None
) -> [np.ndarray, np.ndarray]:
    """ Compute confusion matrix.
    
    Args:
        learn: trained model
        dl: dataloader with images and ground truth masks 
        thres: threshold under which to reject predicted label and set to class-id 0 instead.

    Return:
        The un-normalized and the normalized confusion matrices.
    """
    y_gts = []
    y_preds = []

    # Loop over all images
    for im_path, gt_path in zip(dl.x.items, dl.y.items):
        pred_mask, _ = predict(im_path, learn, thres)

        # load ground truth and resize to be same size as predited mask
        gt_mask = PIL.Image.open(gt_path)
        gt_mask = gt_mask.resize(pred_mask.shape[::-1], resample=PIL.Image.NEAREST)
        gt_mask = np.asarray(gt_mask)

        # Store predicted and ground truth labels
        assert gt_mask.shape[0] == pred_mask.shape[0]
        assert gt_mask.shape[1] == pred_mask.shape[1]
        y_gts.extend(gt_mask.flatten())
        y_preds.extend(pred_mask.flatten())

    # Compute confusion matrices
    cmat = sk_confusion_matrix(y_gts, y_preds)
    cmat_norm = sk_confusion_matrix(y_gts, y_preds, normalize="true")

    return cmat, cmat_norm


def print_accuracies(
    cmat: np.ndarray, cmat_norm: np.ndarray, classes: List[str]
) -> [int, int]:
    """ Print accuracies per class, and the overall class-averaged accuracy. """
    class_accs = 100.0 * np.diag(cmat_norm)
    overall_acc = 100.0 * np.diag(cmat).sum() / cmat.sum()
    print(f"Overall accuracy: {overall_acc:3.2f}%")
    print(f"Class-averaged accuracy: {np.mean(class_accs):3.2f}%")
    for acc, cla in zip(class_accs, classes):
        print(f"\tClass {cla:>15} has accuracy: {acc:2.2f}%")

    return overall_acc, class_accs