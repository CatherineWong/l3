#!/bin/sh

python -u ../../rl.py \
  --train \
  --n_epochs=250 \
  --predict_hyp=true \
  --infer_hyp=true \
  --use_expert=true \
  > train.out \
  2> train.err

