# Results

## Initial dev — pooled training

| task      | labels      | family  | model                   | arm          | regime     | train                                   | fit       | eval | seed | epochs | batch | lr     | LoRA | all    | english | sinhala | singlish | tamil  | tamilish |
|:----------|:------------|:--------|:------------------------|:-------------|:-----------|:----------------------------------------|:----------|:-----|-----:|:-------|:------|:-------|:-----|:-------|:--------|:--------|:---------|:-------|:---------|
| intent    | same-labels | decoder | gemma-3-270m            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9038 | —       | —       | —        | —      | —        |
| intent    | same-labels | probe   | canine-c-probe-cls      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4734 | 0.3252  | 0.5448  | 0.5457   | 0.4598 | 0.4851   |
| intent    | same-labels | probe   | canine-c-probe-mean     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.641  | 0.591   | 0.6748  | 0.6848   | 0.6087 | 0.6421   |
| intent    | same-labels | probe   | gemma-3-1b-probe-last   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8408 | 0.8425  | 0.8675  | 0.8138   | 0.8776 | 0.8009   |
| intent    | same-labels | probe   | gemma-3-1b-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.857  | 0.8557  | 0.8762  | 0.8362   | 0.8892 | 0.8278   |
| intent    | same-labels | probe   | gemma-3-270m-probe-last | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7918 | 0.8071  | 0.8379  | 0.7749   | 0.8057 | 0.7334   |
| intent    | same-labels | probe   | gemma-3-270m-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.799  | 0.7743  | 0.8199  | 0.8047   | 0.841  | 0.7535   |
| intent    | same-labels | probe   | labse-probe-cls         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.859  | 0.8781  | 0.8925  | 0.845    | 0.8542 | 0.8254   |
| intent    | same-labels | probe   | labse-probe-mean        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8614 | 0.878   | 0.8883  | 0.8507   | 0.8533 | 0.8368   |
| intent    | same-labels | probe   | mmbert-probe-cls        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8054 | 0.8475  | 0.8075  | 0.7879   | 0.8164 | 0.7671   |
| intent    | same-labels | probe   | mmbert-probe-mean       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.817  | 0.8481  | 0.8455  | 0.779    | 0.859  | 0.7514   |
| intent    | same-labels | probe   | twhin-bert-probe-cls    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.777  | 0.7885  | 0.8213  | 0.7638   | 0.7724 | 0.7402   |
| intent    | same-labels | probe   | twhin-bert-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8249 | 0.8251  | 0.8482  | 0.8278   | 0.8042 | 0.8194   |
| intent    | same-labels | probe   | xlmr-base-probe-cls     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7906 | 0.8474  | 0.8211  | 0.7494   | 0.8234 | 0.7089   |
| intent    | same-labels | probe   | xlmr-base-probe-mean    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8074 | 0.8359  | 0.8427  | 0.7803   | 0.8338 | 0.7432   |
| priority  | same-labels | decoder | gemma-3-270m            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.904  | —       | —       | —        | —      | —        |
| priority  | same-labels | encoder | canine-c                | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 32    | 2e-05  | n/a  | 0.8786 | —       | —       | —        | —      | —        |
| priority  | same-labels | probe   | canine-c-probe-cls      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6181 | 0.6005  | 0.6371  | 0.6276   | 0.6178 | 0.6078   |
| priority  | same-labels | probe   | canine-c-probe-mean     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6565 | 0.6488  | 0.678   | 0.6646   | 0.6384 | 0.6529   |
| priority  | same-labels | probe   | gemma-3-1b-probe-last   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7864 | 0.8291  | 0.7873  | 0.785    | 0.7794 | 0.753    |
| priority  | same-labels | probe   | gemma-3-1b-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7887 | 0.8252  | 0.7985  | 0.7935   | 0.7822 | 0.7453   |
| priority  | same-labels | probe   | gemma-3-270m-probe-last | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7255 | 0.8013  | 0.7069  | 0.7517   | 0.6687 | 0.7041   |
| priority  | same-labels | probe   | gemma-3-270m-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.719  | 0.7797  | 0.6829  | 0.7493   | 0.6793 | 0.7112   |
| priority  | same-labels | probe   | labse-probe-cls         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8265 | 0.8576  | 0.8678  | 0.7953   | 0.8462 | 0.7695   |
| priority  | same-labels | probe   | labse-probe-mean        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8247 | 0.8468  | 0.863   | 0.796    | 0.8489 | 0.7724   |
| priority  | same-labels | probe   | mmbert-probe-cls        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7694 | 0.8161  | 0.7872  | 0.7381   | 0.788  | 0.7217   |
| priority  | same-labels | probe   | mmbert-probe-mean       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7719 | 0.8233  | 0.7821  | 0.7441   | 0.7947 | 0.7195   |
| priority  | same-labels | probe   | twhin-bert-probe-cls    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7283 | 0.7732  | 0.7406  | 0.7237   | 0.7038 | 0.7031   |
| priority  | same-labels | probe   | twhin-bert-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7685 | 0.7891  | 0.7803  | 0.7686   | 0.7589 | 0.7463   |
| priority  | same-labels | probe   | xlmr-base-probe-cls     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7609 | 0.802   | 0.7911  | 0.7254   | 0.7843 | 0.7058   |
| priority  | same-labels | probe   | xlmr-base-probe-mean    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.7643 | 0.7945  | 0.802   | 0.7367   | 0.7776 | 0.7141   |
| sentiment | v5          | decoder | gemma-3-270m            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.5611 | —       | —       | —        | —      | —        |
| sentiment | v5          | encoder | canine-c                | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 32    | 2e-05  | n/a  | 0.5323 | —       | —       | —        | —      | —        |
| sentiment | v5          | encoder | labse-lora              | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a    | n/a  | —      | 0.3821  | 0.4767  | 0.3944   | 0.4242 | 0.3621   |
| sentiment | v5          | probe   | canine-c-probe-cls      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.2807 | 0.2939  | 0.2269  | 0.3274   | 0.2703 | 0.2925   |
| sentiment | v5          | probe   | canine-c-probe-mean     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3164 | 0.3174  | 0.3259  | 0.3312   | 0.2866 | 0.3228   |
| sentiment | v5          | probe   | gemma-3-1b-probe-last   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4391 | 0.45    | 0.4324  | 0.4375   | 0.4552 | 0.4226   |
| sentiment | v5          | probe   | gemma-3-1b-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4122 | 0.5417  | 0.4086  | 0.3864   | 0.4188 | 0.3409   |
| sentiment | v5          | probe   | gemma-3-270m-probe-last | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3539 | 0.4094  | 0.3478  | 0.3663   | 0.3193 | 0.3438   |
| sentiment | v5          | probe   | gemma-3-270m-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.325  | 0.4418  | 0.3046  | 0.3529   | 0.2782 | 0.2941   |
| sentiment | v5          | probe   | labse-probe-cls         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4666 | 0.5463  | 0.5377  | 0.4      | 0.4907 | 0.4028   |
| sentiment | v5          | probe   | labse-probe-mean        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4563 | 0.5075  | 0.514   | 0.4029   | 0.5049 | 0.3929   |
| sentiment | v5          | probe   | mmbert-probe-cls        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3779 | 0.4762  | 0.361   | 0.3553   | 0.3901 | 0.3273   |
| sentiment | v5          | probe   | mmbert-probe-mean       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4137 | 0.5673  | 0.4055  | 0.3849   | 0.4014 | 0.3545   |
| sentiment | v5          | probe   | twhin-bert-probe-cls    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3668 | 0.386   | 0.3851  | 0.3684   | 0.3631 | 0.3354   |
| sentiment | v5          | probe   | twhin-bert-probe-mean   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3828 | 0.4167  | 0.3984  | 0.3612   | 0.3849 | 0.3579   |
| sentiment | v5          | probe   | xlmr-base-probe-cls     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3849 | 0.4959  | 0.4148  | 0.3668   | 0.3709 | 0.3058   |
| sentiment | v5          | probe   | xlmr-base-probe-mean    | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4068 | 0.48    | 0.4615  | 0.3793   | 0.4075 | 0.3279   |

## Initial dev — mono training

| task      | labels      | family   | model                    | arm          | regime   | train    | fit       | eval | seed | epochs | batch | lr    | LoRA | language | score  |
|:----------|:------------|:---------|:-------------------------|:-------------|:---------|:---------|:----------|:-----|-----:|:-------|:------|:------|:-----|:---------|:-------|
| priority  | same-labels | baseline | intent-chained           | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8931 |
| priority  | same-labels | baseline | intent-lookup-oracle     | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.9147 |
| priority  | same-labels | baseline | majority                 | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.2302 |
| priority  | same-labels | baseline | tfidf-cnb                | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8622 |
| priority  | same-labels | baseline | tfidf-cnb                | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8622 |
| priority  | same-labels | baseline | tfidf-cnb                | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8536 |
| priority  | same-labels | baseline | tfidf-logreg             | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8997 |
| priority  | same-labels | baseline | tfidf-logreg             | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8827 |
| priority  | same-labels | baseline | tfidf-logreg             | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8937 |
| priority  | same-labels | baseline | tfidf-sgd                | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8724 |
| priority  | same-labels | baseline | tfidf-sgd                | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8667 |
| priority  | same-labels | baseline | tfidf-sgd                | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8647 |
| priority  | same-labels | baseline | tfidf-svm                | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8964 |
| priority  | same-labels | baseline | tfidf-svm                | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8999 |
| priority  | same-labels | baseline | tfidf-svm                | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8946 |
| sentiment | v5          | baseline | majority                 | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.0    |
| sentiment | v5          | encoder  | labse                    | class_weight | mono-fit | english  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | english  | 0.6667 |
| sentiment | v5          | encoder  | labse-lora               | class_weight | mono-fit | english  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | english  | 0.3226 |
| sentiment | v5          | encoder  | twhin-bert               | class_weight | mono-fit | english  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | english  | 0.6438 |
| sentiment | v5          | encoder  | xlmr-base                | class_weight | mono-fit | english  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | english  | 0.5752 |
| intent    | same-labels | probe    | sinbert-large-probe-cls  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6318 |
| intent    | same-labels | probe    | sinbert-large-probe-mean | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6694 |
| intent    | same-labels | probe    | sinhalaberto-probe-cls   | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7454 |
| intent    | same-labels | probe    | sinhalaberto-probe-mean  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7782 |
| priority  | same-labels | baseline | intent-chained           | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9011 |
| priority  | same-labels | baseline | intent-lookup-oracle     | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9147 |
| priority  | same-labels | baseline | majority                 | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.2302 |
| priority  | same-labels | baseline | tfidf-cnb                | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8639 |
| priority  | same-labels | baseline | tfidf-cnb                | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8639 |
| priority  | same-labels | baseline | tfidf-cnb                | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8569 |
| priority  | same-labels | baseline | tfidf-logreg             | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9001 |
| priority  | same-labels | baseline | tfidf-logreg             | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8891 |
| priority  | same-labels | baseline | tfidf-logreg             | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9062 |
| priority  | same-labels | baseline | tfidf-sgd                | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8836 |
| priority  | same-labels | baseline | tfidf-sgd                | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8852 |
| priority  | same-labels | baseline | tfidf-sgd                | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8891 |
| priority  | same-labels | baseline | tfidf-svm                | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9079 |
| priority  | same-labels | baseline | tfidf-svm                | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.907  |
| priority  | same-labels | baseline | tfidf-svm                | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9025 |
| priority  | same-labels | probe    | sinbert-large-probe-cls  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7531 |
| priority  | same-labels | probe    | sinbert-large-probe-mean | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7685 |
| priority  | same-labels | probe    | sinhalaberto-probe-cls   | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7657 |
| priority  | same-labels | probe    | sinhalaberto-probe-mean  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7856 |
| sentiment | v5          | baseline | majority                 | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.0    |
| sentiment | v5          | encoder  | labse                    | class_weight | mono-fit | sinhala  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | sinhala  | 0.6963 |
| sentiment | v5          | encoder  | labse-lora               | class_weight | mono-fit | sinhala  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | sinhala  | 0.3223 |
| sentiment | v5          | encoder  | twhin-bert               | class_weight | mono-fit | sinhala  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | sinhala  | 0.563  |
| sentiment | v5          | encoder  | xlmr-base                | class_weight | mono-fit | sinhala  | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | sinhala  | 0.5333 |
| sentiment | v5          | probe    | sinbert-large-probe-cls  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.3612 |
| sentiment | v5          | probe    | sinbert-large-probe-mean | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4145 |
| sentiment | v5          | probe    | sinhalaberto-probe-cls   | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4227 |
| sentiment | v5          | probe    | sinhalaberto-probe-mean  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4646 |
| priority  | same-labels | baseline | intent-chained           | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.904  |
| priority  | same-labels | baseline | intent-lookup-oracle     | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9147 |
| priority  | same-labels | baseline | majority                 | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.2302 |
| priority  | same-labels | baseline | tfidf-cnb                | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8641 |
| priority  | same-labels | baseline | tfidf-cnb                | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8641 |
| priority  | same-labels | baseline | tfidf-cnb                | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8667 |
| priority  | same-labels | baseline | tfidf-logreg             | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9017 |
| priority  | same-labels | baseline | tfidf-logreg             | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8852 |
| priority  | same-labels | baseline | tfidf-logreg             | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9068 |
| priority  | same-labels | baseline | tfidf-sgd                | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.886  |
| priority  | same-labels | baseline | tfidf-sgd                | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8964 |
| priority  | same-labels | baseline | tfidf-sgd                | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8915 |
| priority  | same-labels | baseline | tfidf-svm                | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9115 |
| priority  | same-labels | baseline | tfidf-svm                | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9086 |
| priority  | same-labels | baseline | tfidf-svm                | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9068 |
| sentiment | v5          | baseline | majority                 | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.0    |
| sentiment | v5          | encoder  | labse                    | class_weight | mono-fit | singlish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | singlish | 0.6303 |
| sentiment | v5          | encoder  | labse-lora               | class_weight | mono-fit | singlish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | singlish | 0.2629 |
| sentiment | v5          | encoder  | twhin-bert               | class_weight | mono-fit | singlish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | singlish | 0.5373 |
| sentiment | v5          | encoder  | xlmr-base                | class_weight | mono-fit | singlish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | singlish | 0.3626 |
| priority  | same-labels | baseline | intent-chained           | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8921 |
| priority  | same-labels | baseline | intent-lookup-oracle     | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9147 |
| priority  | same-labels | baseline | majority                 | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2302 |
| priority  | same-labels | baseline | tfidf-cnb                | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8536 |
| priority  | same-labels | baseline | tfidf-cnb                | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8536 |
| priority  | same-labels | baseline | tfidf-cnb                | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8419 |
| priority  | same-labels | baseline | tfidf-logreg             | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8966 |
| priority  | same-labels | baseline | tfidf-logreg             | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8821 |
| priority  | same-labels | baseline | tfidf-logreg             | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8966 |
| priority  | same-labels | baseline | tfidf-sgd                | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8845 |
| priority  | same-labels | baseline | tfidf-sgd                | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8884 |
| priority  | same-labels | baseline | tfidf-sgd                | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8774 |
| priority  | same-labels | baseline | tfidf-svm                | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9109 |
| priority  | same-labels | baseline | tfidf-svm                | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9017 |
| priority  | same-labels | baseline | tfidf-svm                | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.902  |
| sentiment | v5          | baseline | majority                 | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.0    |
| sentiment | v5          | encoder  | labse                    | class_weight | mono-fit | tamil    | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamil    | 0.6803 |
| sentiment | v5          | encoder  | labse-lora               | class_weight | mono-fit | tamil    | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamil    | 0.3219 |
| sentiment | v5          | encoder  | twhin-bert               | class_weight | mono-fit | tamil    | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamil    | 0.5811 |
| sentiment | v5          | encoder  | xlmr-base                | class_weight | mono-fit | tamil    | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamil    | 0.5436 |
| priority  | same-labels | baseline | intent-chained           | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8945 |
| priority  | same-labels | baseline | intent-lookup-oracle     | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9147 |
| priority  | same-labels | baseline | majority                 | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.2302 |
| priority  | same-labels | baseline | tfidf-cnb                | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8701 |
| priority  | same-labels | baseline | tfidf-cnb                | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8701 |
| priority  | same-labels | baseline | tfidf-cnb                | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8739 |
| priority  | same-labels | baseline | tfidf-logreg             | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8941 |
| priority  | same-labels | baseline | tfidf-logreg             | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8847 |
| priority  | same-labels | baseline | tfidf-logreg             | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8993 |
| priority  | same-labels | baseline | tfidf-sgd                | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8885 |
| priority  | same-labels | baseline | tfidf-sgd                | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8908 |
| priority  | same-labels | baseline | tfidf-sgd                | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8912 |
| priority  | same-labels | baseline | tfidf-svm                | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9036 |
| priority  | same-labels | baseline | tfidf-svm                | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.899  |
| priority  | same-labels | baseline | tfidf-svm                | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9031 |
| sentiment | v5          | baseline | majority                 | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.0    |
| sentiment | v5          | encoder  | labse                    | class_weight | mono-fit | tamilish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamilish | 0.5526 |
| sentiment | v5          | encoder  | labse-lora               | class_weight | mono-fit | tamilish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamilish | 0.2739 |
| sentiment | v5          | encoder  | twhin-bert               | class_weight | mono-fit | tamilish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamilish | 0.5    |
| sentiment | v5          | encoder  | xlmr-base                | class_weight | mono-fit | tamilish | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | tamilish | 0.3364 |

## Initial dev — transfer training

| task      | labels      | family   | model         | arm          | regime       | train   | fit       | eval | seed | epochs | batch | lr    | LoRA | language | score  |
|:----------|:------------|:---------|:--------------|:-------------|:-------------|:--------|:----------|:-----|-----:|:-------|:------|:------|:-----|:---------|:-------|
| priority  | same-labels | encoder  | sinbert-large | class_weight | transfer-fit | sinhala | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | all      | 0.4939 |
| priority  | same-labels | encoder  | sinhalaberto  | class_weight | transfer-fit | sinhala | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | all      | 0.5573 |
| sentiment | v5          | encoder  | sinbert-large | class_weight | transfer-fit | sinhala | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | all      | 0.1238 |
| sentiment | v5          | encoder  | sinhalaberto  | class_weight | transfer-fit | sinhala | train     | dev  |   42 | 3      | 32    | 2e-05 | n/a  | all      | 0.173  |
| priority  | same-labels | baseline | tfidf-cnb     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6958 |
| priority  | same-labels | baseline | tfidf-cnb     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6958 |
| priority  | same-labels | baseline | tfidf-cnb     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6788 |
| priority  | same-labels | baseline | tfidf-logreg  | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7038 |
| priority  | same-labels | baseline | tfidf-logreg  | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6741 |
| priority  | same-labels | baseline | tfidf-logreg  | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.7141 |
| priority  | same-labels | baseline | tfidf-sgd     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.595  |
| priority  | same-labels | baseline | tfidf-sgd     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6043 |
| priority  | same-labels | baseline | tfidf-sgd     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.611  |
| priority  | same-labels | baseline | tfidf-svm     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.696  |
| priority  | same-labels | baseline | tfidf-svm     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6915 |
| priority  | same-labels | baseline | tfidf-svm     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6966 |
| priority  | same-labels | baseline | tfidf-cnb     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7579 |
| priority  | same-labels | baseline | tfidf-cnb     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7579 |
| priority  | same-labels | baseline | tfidf-cnb     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7041 |
| priority  | same-labels | baseline | tfidf-logreg  | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7296 |
| priority  | same-labels | baseline | tfidf-logreg  | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6491 |
| priority  | same-labels | baseline | tfidf-logreg  | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7256 |
| priority  | same-labels | baseline | tfidf-sgd     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5387 |
| priority  | same-labels | baseline | tfidf-sgd     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5441 |
| priority  | same-labels | baseline | tfidf-sgd     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5333 |
| priority  | same-labels | baseline | tfidf-svm     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.7009 |
| priority  | same-labels | baseline | tfidf-svm     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6899 |
| priority  | same-labels | baseline | tfidf-svm     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.709  |
| priority  | same-labels | baseline | tfidf-cnb     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.1739 |
| priority  | same-labels | baseline | tfidf-cnb     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.1739 |
| priority  | same-labels | baseline | tfidf-cnb     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.1743 |
| priority  | same-labels | baseline | tfidf-logreg  | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2834 |
| priority  | same-labels | baseline | tfidf-logreg  | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2749 |
| priority  | same-labels | baseline | tfidf-logreg  | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2919 |
| priority  | same-labels | baseline | tfidf-sgd     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2659 |
| priority  | same-labels | baseline | tfidf-sgd     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2659 |
| priority  | same-labels | baseline | tfidf-sgd     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2659 |
| priority  | same-labels | baseline | tfidf-svm     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2825 |
| priority  | same-labels | baseline | tfidf-svm     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2827 |
| priority  | same-labels | baseline | tfidf-svm     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.2913 |
| priority  | same-labels | baseline | tfidf-cnb     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.7174 |
| priority  | same-labels | baseline | tfidf-cnb     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.7174 |
| priority  | same-labels | baseline | tfidf-cnb     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.7224 |
| priority  | same-labels | baseline | tfidf-logreg  | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.7283 |
| priority  | same-labels | baseline | tfidf-logreg  | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6582 |
| priority  | same-labels | baseline | tfidf-logreg  | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.7302 |
| priority  | same-labels | baseline | tfidf-sgd     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5147 |
| priority  | same-labels | baseline | tfidf-sgd     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5125 |
| priority  | same-labels | baseline | tfidf-sgd     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5196 |
| priority  | same-labels | baseline | tfidf-svm     | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6846 |
| priority  | same-labels | baseline | tfidf-svm     | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.674  |
| priority  | same-labels | baseline | tfidf-svm     | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6985 |

## Initial test — pooled training

| task      | labels      | family  | model                         | arm          | regime     | train                                   | fit       | eval | seed | epochs | batch | lr    | LoRA |    all | english | sinhala | singlish | tamil | tamilish |
|:----------|:------------|:--------|:------------------------------|:-------------|:-----------|:----------------------------------------|:----------|:-----|-----:|:-------|:------|:------|:-----|-------:|:--------|:--------|:---------|:------|:---------|
| intent    | same-labels | probe   | labse-ft-priority-probe-cls   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7962 | —       | —       | —        | —     | —        |
| intent    | same-labels | probe   | labse-ft-priority-probe-mean  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7971 | —       | —       | —        | —     | —        |
| intent    | same-labels | probe   | labse-ft-sentiment-probe-cls  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7594 | —       | —       | —        | —     | —        |
| intent    | same-labels | probe   | labse-ft-sentiment-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7676 | —       | —       | —        | —     | —        |
| intent    | same-labels | probe   | labse-probe-cls               | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7773 | —       | —       | —        | —     | —        |
| intent    | same-labels | probe   | labse-probe-mean              | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.7822 | —       | —       | —        | —     | —        |
| priority  | same-labels | encoder | labse                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev | test |   42 | 3      | 32    | 2e-05 | n/a  |   0.89 | —       | —       | —        | —     | —        |
| priority  | same-labels | encoder | mmbert                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev | test |   42 | 3      | 32    | 2e-05 | n/a  | 0.8887 | —       | —       | —        | —     | —        |
| priority  | same-labels | encoder | xlmr-base                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev | test |   42 | 3      | 32    | 2e-05 | n/a  | 0.8872 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-ft-priority-probe-cls   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.8825 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-ft-priority-probe-mean  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.8816 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-ft-sentiment-probe-cls  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  |  0.799 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-ft-sentiment-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  |  0.804 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-probe-cls               | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.8008 | —       | —       | —        | —     | —        |
| priority  | same-labels | probe   | labse-probe-mean              | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.8015 | —       | —       | —        | —     | —        |
| sentiment | v5          | encoder | canine-c                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev | test |   42 | 3      | 32    | 2e-05 | n/a  | 0.4702 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-ft-priority-probe-cls   | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.3828 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-ft-priority-probe-mean  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.3867 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-ft-sentiment-probe-cls  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.4633 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-ft-sentiment-probe-mean | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  |  0.481 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-probe-cls               | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.3682 | —       | —       | —        | —     | —        |
| sentiment | v5          | probe   | labse-probe-mean              | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | test |   42 | n/a    | n/a   | n/a   | n/a  | 0.3735 | —       | —       | —        | —     | —        |

## Official-split intent — early architecture screen

| model               | english | sinhala | singlish |  tamil | tamilish |    all |
|:--------------------|:--------|:--------|:---------|-------:|---------:|-------:|
| LaBSE               | 0.9413  | 0.9295  | 0.9065   | 0.9327 |   0.7057 | 0.8854 |
| XLM-R base          | 0.9388  | 0.9242  | 0.9003   | 0.9174 |   0.7204 | 0.8829 |
| IndicBERT           | —       | —       | —        | 0.8981 |   0.6125 | 0.7624 |
| MuRIL               | —       | —       | —        | 0.6601 |   0.5762 |  0.621 |
| Linear SVM          | 0.9098  | 0.8275  | 0.8649   | 0.8635 |   0.6105 | 0.8318 |
| Logistic regression | 0.9048  | 0.8308  | 0.8607   | 0.8422 |   0.5905 | 0.8216 |

## Later dev — pooled training

| task      | labels      | family            | model                            | arm          | regime     | train                                   | fit       | eval | seed | epochs | batch | lr     | LoRA |    all | english | sinhala | singlish | tamil  | tamilish |
|:----------|:------------|:------------------|:---------------------------------|:-------------|:-----------|:----------------------------------------|:----------|:-----|-----:|:-------|:------|:-------|:-----|-------:|:--------|:--------|:---------|:-------|:---------|
| intent    | same-labels | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.0005 | 0.0005  | 0.0005  | 0.0005   | 0.0005 | 0.0005   |
| intent    | same-labels | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8048 | —       | —       | —        | —      | —        |
| intent    | same-labels | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8048 | 0.7703  | 0.7972  | 0.8035   | 0.8167 | 0.8291   |
| intent    | same-labels | baseline          | tfidf-knn                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8412 | 0.8152  | 0.8506  | 0.8506   | 0.8359 | 0.8534   |
| intent    | same-labels | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9104 | —       | —       | —        | —      | —        |
| intent    | same-labels | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.912 | 0.8922  | 0.9181  | 0.9181   | 0.9127 | 0.9188   |
| intent    | same-labels | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9062 | 0.8864  | 0.9135  | 0.907    | 0.897  | 0.9268   |
| intent    | same-labels | baseline          | tfidf-rf                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8788 | 0.8629  | 0.878   | 0.8843   | 0.884  | 0.8852   |
| intent    | same-labels | baseline          | tfidf-ridge                      | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8775 | 0.8563  | 0.8851  | 0.8718   | 0.8817 | 0.8906   |
| intent    | same-labels | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.905 | —       | —       | —        | —      | —        |
| intent    | same-labels | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9092 | 0.8939  | 0.9145  | 0.908    | 0.9034 | 0.9266   |
| intent    | same-labels | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9201 | —       | —       | —        | —      | —        |
| intent    | same-labels | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9202 | 0.9068  | 0.9258  | 0.9252   | 0.9155 | 0.9288   |
| intent    | same-labels | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9232 | —       | —       | —        | —      | —        |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9211 | —       | —       | —        | —      | —        |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9284 | —       | —       | —        | —      | —        |
| intent    | same-labels | encoder           | indicbert                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9104 | 0.9183  | 0.9     | 0.9069   | 0.929  | 0.8982   |
| intent    | same-labels | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9293 | 0.9309  | 0.9405  | 0.924    | 0.9342 | 0.917    |
| intent    | same-labels | encoder           | mmbert                           | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9294 | 0.9397  | 0.9371  | 0.9208   | 0.9375 | 0.9122   |
| intent    | same-labels | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.8703 | 0.9003  | 0.7633  | 0.8879   | 0.9009 | 0.9023   |
| intent    | same-labels | encoder           | twhin-bert                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9082 | 0.912   | 0.9212  | 0.8999   | 0.9087 | 0.8996   |
| intent    | same-labels | encoder           | xlmr-base                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9219 | 0.9268  | 0.9361  | 0.9075   | 0.924  | 0.9155   |
| priority  | same-labels | baseline          | intent-chained                   | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8964 | 0.8919  | 0.9025  | 0.901    | 0.8865 | 0.9002   |
| priority  | same-labels | baseline          | intent-lookup-oracle             | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9147 | 0.9147  | 0.9147  | 0.9147   | 0.9147 | 0.9147   |
| priority  | same-labels | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.2302 | 0.2302  | 0.2302  | 0.2302   | 0.2302 | 0.2302   |
| priority  | same-labels | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8606 | 0.8572  | 0.8628  | 0.8625   | 0.8588 | 0.8618   |
| priority  | same-labels | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8606 | 0.8572  | 0.8628  | 0.8625   | 0.8588 | 0.8618   |
| priority  | same-labels | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8586 | 0.8553  | 0.8571  | 0.8585   | 0.8573 | 0.8651   |
| priority  | same-labels | baseline          | tfidf-knn                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8823 | 0.8812  | 0.8827  | 0.8861   | 0.8762 | 0.885    |
| priority  | same-labels | baseline          | tfidf-knn                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8823 | 0.8812  | 0.8827  | 0.8861   | 0.8762 | 0.885    |
| priority  | same-labels | baseline          | tfidf-knn                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8671 | 0.8561  | 0.868   | 0.8706   | 0.858  | 0.8829   |
| priority  | same-labels | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8947 | 0.8884  | 0.8984  | 0.8939   | 0.8909 | 0.9017   |
| priority  | same-labels | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8884 | 0.886   | 0.8912  | 0.8907   | 0.8847 | 0.8894   |
| priority  | same-labels | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8989 | 0.8927  | 0.9011  | 0.9037   | 0.8986 | 0.8986   |
| priority  | same-labels | baseline          | tfidf-mnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8673 | 0.8667  | 0.8675  | 0.8655   | 0.8666 | 0.8706   |
| priority  | same-labels | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8673 | 0.8667  | 0.8675  | 0.8655   | 0.8666 | 0.8706   |
| priority  | same-labels | baseline          | tfidf-mnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8672 | 0.8587  | 0.8666  | 0.8637   | 0.8692 | 0.8781   |
| priority  | same-labels | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.885 | 0.8873  | 0.8777  | 0.8913   | 0.8871 | 0.8822   |
| priority  | same-labels | baseline          | tfidf-rf                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8707 | 0.8728  | 0.8802  | 0.8781   | 0.8633 | 0.8584   |
| priority  | same-labels | baseline          | tfidf-rf                         | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.886 | 0.8876  | 0.8865  | 0.8936   | 0.8825 | 0.8797   |
| priority  | same-labels | baseline          | tfidf-ridge                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9023 | 0.891   | 0.9067  | 0.9071   | 0.8994 | 0.9074   |
| priority  | same-labels | baseline          | tfidf-ridge                      | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9009 | 0.8907  | 0.9014  | 0.9043   | 0.9019 | 0.9057   |
| priority  | same-labels | baseline          | tfidf-ridge                      | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8994 | 0.8907  | 0.899   | 0.9092   | 0.8933 | 0.905    |
| priority  | same-labels | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8933 | 0.8721  | 0.9085  | 0.9024   | 0.8806 | 0.9021   |
| priority  | same-labels | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8925 | 0.8813  | 0.9047  | 0.9028   | 0.877  | 0.8962   |
| priority  | same-labels | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8951 | 0.886   | 0.9049  | 0.9035   | 0.8854 | 0.8955   |
| priority  | same-labels | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9013 | 0.8939  | 0.907   | 0.9049   | 0.8995 | 0.901    |
| priority  | same-labels | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.9008 | 0.8938  | 0.9089  | 0.9064   | 0.8949 | 0.9002   |
| priority  | same-labels | baseline          | tfidf-svm                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.8998 | 0.8956  | 0.907   | 0.9019   | 0.8919 | 0.9023   |
| priority  | same-labels | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  |  0.917 | —       | —       | —        | —      | —        |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9152 | —       | —       | —        | —      | —        |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.9186 | —       | —       | —        | —      | —        |
| priority  | same-labels | encoder           | indicbert                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9088 | 0.9253  | 0.8928  | 0.9137   | 0.9198 | 0.8922   |
| priority  | same-labels | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9167 | 0.926   | 0.9251  | 0.9074   | 0.9203 | 0.9046   |
| priority  | same-labels | encoder           | mmbert                           | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  |  0.913 | 0.9279  | 0.9174  | 0.9122   | 0.9127 | 0.8948   |
| priority  | same-labels | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.8957 | 0.9223  | 0.8313  | 0.9108   | 0.9109 | 0.9031   |
| priority  | same-labels | encoder           | twhin-bert                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.8987 | 0.903   | 0.8987  | 0.9034   | 0.9004 | 0.8878   |
| priority  | same-labels | encoder           | xlmr-base                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.9155 | 0.9253  | 0.9258  | 0.9089   | 0.9168 | 0.9005   |
| sentiment | v5          | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |    0.0 | 0.0     | 0.0     | 0.0      | 0.0    | 0.0      |
| sentiment | v8          | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.461 | 0.4396  | 0.4912  | 0.5541   | 0.3864 | 0.4795   |
| sentiment | v5          | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4281 | 0.4409  | 0.4409  | 0.5246   | 0.3609 | 0.4226   |
| sentiment | v8          | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.461 | 0.4396  | 0.4912  | 0.5541   | 0.3864 | 0.4795   |
| sentiment | v5          | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4281 | 0.4409  | 0.4409  | 0.5246   | 0.3609 | 0.4226   |
| sentiment | v8          | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4654 | 0.452   | 0.4664  | 0.4748   | 0.4667 | 0.469    |
| sentiment | v5          | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |  0.442 | 0.428   | 0.4385  | 0.475    | 0.4331 | 0.438    |
| sentiment | v5          | baseline          | tfidf-knn                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.1499 | 0.1818  | 0.175   | 0.1538   | 0.08   | 0.1558   |
| sentiment | v5          | baseline          | tfidf-knn                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.1499 | 0.1818  | 0.175   | 0.1538   | 0.08   | 0.1558   |
| sentiment | v5          | baseline          | tfidf-knn                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4487 | 0.4622  | 0.453   | 0.4268   | 0.4444 | 0.4581   |
| sentiment | v8          | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5937 | 0.5948  | 0.5882  | 0.5946   | 0.5841 | 0.6075   |
| sentiment | v5          | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5742 | 0.5969  | 0.5914  | 0.5926   | 0.5445 | 0.5455   |
| sentiment | v8          | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4787 | 0.4603  | 0.5     | 0.5041   | 0.4576 | 0.4706   |
| sentiment | v5          | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.2676 | 0.3133  | 0.2278  | 0.3256   | 0.241  | 0.225    |
| sentiment | v8          | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6148 | 0.6038  | 0.6058  | 0.601    | 0.6354 | 0.631    |
| sentiment | v5          | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5854 | 0.5476  | 0.5882  | 0.6303   | 0.5854 | 0.5752   |
| sentiment | v5          | baseline          | tfidf-mnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5297 | 0.4851  | 0.5455  | 0.5783   | 0.514  | 0.5368   |
| sentiment | v5          | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5297 | 0.4851  | 0.5455  | 0.5783   | 0.514  | 0.5368   |
| sentiment | v5          | baseline          | tfidf-mnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  |   0.45 | 0.4215  | 0.4667  | 0.4762   | 0.4463 | 0.4426   |
| sentiment | v5          | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4559 | 0.4444  | 0.4587  | 0.4528   | 0.4602 | 0.463    |
| sentiment | v5          | baseline          | tfidf-rf                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.2632 | 0.2683  | 0.3059  | 0.2892   | 0.2093 | 0.2439   |
| sentiment | v5          | baseline          | tfidf-rf                         | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.2597 | 0.1905  | 0.3111  | 0.3441   | 0.1667 | 0.2727   |
| sentiment | v5          | baseline          | tfidf-ridge                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6109 | 0.6049  | 0.625   | 0.6203   | 0.6234 | 0.5806   |
| sentiment | v5          | baseline          | tfidf-ridge                      | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.3728 | 0.3297  | 0.3736  | 0.4348   | 0.3333 | 0.3913   |
| sentiment | v5          | baseline          | tfidf-ridge                      | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5794 | 0.576   | 0.6131  | 0.6029   | 0.5528 | 0.5469   |
| sentiment | v8          | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5651 | 0.5422  | 0.5769  | 0.575    | 0.6118 | 0.5161   |
| sentiment | v5          | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5282 | 0.544   | 0.5     | 0.5278   | 0.5231 | 0.5484   |
| sentiment | v8          | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5792 | 0.5478  | 0.5906  | 0.5963   | 0.6012 | 0.5578   |
| sentiment | v5          | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5087 | 0.531   | 0.4602  | 0.4909   | 0.521  | 0.5378   |
| sentiment | v8          | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5888 | 0.5926  | 0.6329  | 0.6012   | 0.5974 | 0.5166   |
| sentiment | v5          | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5333 | 0.5714  | 0.5574  | 0.562    | 0.4727 | 0.4956   |
| sentiment | v8          | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6338 | 0.6257  | 0.618   | 0.6264   | 0.6486 | 0.6509   |
| sentiment | v5          | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5901 | 0.6069  | 0.5915  | 0.6187   | 0.6087 | 0.5248   |
| sentiment | v8          | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.6324 | 0.6323  | 0.6443  | 0.6486   | 0.64   | 0.5942   |
| sentiment | v5          | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.4944 | 0.5273  | 0.4906  | 0.4673   | 0.4952 | 0.4906   |
| sentiment | v8          | baseline          | tfidf-svm                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5931 | 0.6012  | 0.6     | 0.5965   | 0.6203 | 0.5455   |
| sentiment | v5          | baseline          | tfidf-svm                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | n/a    | n/a   | n/a    | n/a  | 0.5195 | 0.5405  | 0.5714  | 0.5556   | 0.4643 | 0.4561   |
| sentiment | v8          | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.7098 | —       | —       | —        | —      | —        |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.7046 | —       | —       | —        | —      | —        |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 3      | 16    | 0.0001 | all  | 0.6857 | —       | —       | —        | —      | —        |
| sentiment | v8          | encoder           | indicbert                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  |  0.694 | 0.7543  | 0.6194  | 0.6824   | 0.7657 | 0.6323   |
| sentiment | v8          | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.7579 | 0.8092  | 0.7811  | 0.7134   | 0.7929 | 0.6835   |
| sentiment | v8          | encoder           | mmbert                           | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.6991 | 0.7578  | 0.7205  | 0.6316   | 0.7529 | 0.6242   |
| sentiment | v8          | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.6547 | 0.7407  | 0.507   | 0.6351   | 0.72   | 0.6452   |
| sentiment | v8          | encoder           | twhin-bert                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.6461 | 0.6977  | 0.646   | 0.6289   | 0.6506 | 0.6013   |
| sentiment | v8          | encoder           | xlmr-base                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train     | dev  |   42 | 6      | 32    | 2e-05  | n/a  | 0.6869 | 0.7574  | 0.6905  | 0.6909   | 0.6703 | 0.6272   |

## Later dev — mono training

| task      | labels      | family   | model        | arm          | regime   | train    | fit       | eval | seed | epochs | batch | lr    | LoRA | language | score  |
|:----------|:------------|:---------|:-------------|:-------------|:---------|:---------|:----------|:-----|-----:|:-------|:------|:------|:-----|:---------|:-------|
| intent    | same-labels | baseline | majority     | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.7701 |
| intent    | same-labels | baseline | tfidf-knn    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8359 |
| intent    | same-labels | baseline | tfidf-logreg | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8901 |
| intent    | same-labels | baseline | tfidf-mnb    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8904 |
| intent    | same-labels | baseline | tfidf-rf     | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.86   |
| intent    | same-labels | baseline | tfidf-ridge  | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8565 |
| intent    | same-labels | baseline | tfidf-sgd    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8967 |
| intent    | same-labels | baseline | tfidf-svm    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.9031 |
| priority  | same-labels | baseline | tfidf-knn    | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8796 |
| priority  | same-labels | baseline | tfidf-knn    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8796 |
| priority  | same-labels | baseline | tfidf-mnb    | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8599 |
| priority  | same-labels | baseline | tfidf-mnb    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8599 |
| priority  | same-labels | baseline | tfidf-rf     | ros          | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.8836 |
| priority  | same-labels | baseline | tfidf-ridge  | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.9003 |
| sentiment | v5          | baseline | majority     | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb    | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4737 |
| sentiment | v8          | baseline | tfidf-cnb    | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4737 |
| sentiment | v8          | baseline | tfidf-cnb    | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4746 |
| sentiment | v5          | baseline | tfidf-cnb    | ros          | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4113 |
| sentiment | v5          | baseline | tfidf-knn    | ros          | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4508 |
| sentiment | v8          | baseline | tfidf-logreg | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.633  |
| sentiment | v8          | baseline | tfidf-logreg | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.3091 |
| sentiment | v8          | baseline | tfidf-logreg | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.6473 |
| sentiment | v5          | baseline | tfidf-logreg | ros          | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5698 |
| sentiment | v5          | baseline | tfidf-mnb    | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5567 |
| sentiment | v5          | baseline | tfidf-mnb    | none         | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5567 |
| sentiment | v5          | baseline | tfidf-rf     | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4815 |
| sentiment | v5          | baseline | tfidf-ridge  | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5844 |
| sentiment | v8          | baseline | tfidf-sgd    | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5333 |
| sentiment | v8          | baseline | tfidf-sgd    | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.5103 |
| sentiment | v8          | baseline | tfidf-sgd    | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.4762 |
| sentiment | v5          | baseline | tfidf-sgd    | ros          | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.3429 |
| sentiment | v8          | baseline | tfidf-svm    | class_weight | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.6592 |
| sentiment | v5          | baseline | tfidf-svm    | class_weight | mono-fit | english  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.6015 |
| sentiment | v8          | baseline | tfidf-svm    | none         | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.589  |
| sentiment | v8          | baseline | tfidf-svm    | ros          | mono-fit | english  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | english  | 0.6    |
| sentiment | v5          | encoder  | labse        | class_weight | mono-fit | english  | train     | dev  |   43 | 6      | 32    | 2e-05 | n/a  | english  | 0.6875 |
| intent    | same-labels | baseline | majority     | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8158 |
| intent    | same-labels | baseline | tfidf-knn    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8737 |
| intent    | same-labels | baseline | tfidf-logreg | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.919  |
| intent    | same-labels | baseline | tfidf-mnb    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9166 |
| intent    | same-labels | baseline | tfidf-rf     | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8805 |
| intent    | same-labels | baseline | tfidf-ridge  | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.891  |
| intent    | same-labels | baseline | tfidf-sgd    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9159 |
| intent    | same-labels | baseline | tfidf-svm    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9251 |
| priority  | same-labels | baseline | tfidf-knn    | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8939 |
| priority  | same-labels | baseline | tfidf-knn    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8939 |
| priority  | same-labels | baseline | tfidf-mnb    | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8717 |
| priority  | same-labels | baseline | tfidf-mnb    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8717 |
| priority  | same-labels | baseline | tfidf-rf     | ros          | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.8926 |
| priority  | same-labels | baseline | tfidf-ridge  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.9104 |
| sentiment | v5          | baseline | majority     | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb    | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4891 |
| sentiment | v8          | baseline | tfidf-cnb    | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4891 |
| sentiment | v8          | baseline | tfidf-cnb    | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4589 |
| sentiment | v5          | baseline | tfidf-cnb    | ros          | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4392 |
| sentiment | v5          | baseline | tfidf-knn    | ros          | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4372 |
| sentiment | v8          | baseline | tfidf-logreg | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6075 |
| sentiment | v8          | baseline | tfidf-logreg | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.45   |
| sentiment | v8          | baseline | tfidf-logreg | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.603  |
| sentiment | v5          | baseline | tfidf-logreg | ros          | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6353 |
| sentiment | v5          | baseline | tfidf-mnb    | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.5155 |
| sentiment | v5          | baseline | tfidf-mnb    | none         | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.5155 |
| sentiment | v5          | baseline | tfidf-rf     | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.5043 |
| sentiment | v5          | baseline | tfidf-ridge  | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6316 |
| sentiment | v8          | baseline | tfidf-sgd    | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.5638 |
| sentiment | v8          | baseline | tfidf-sgd    | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.5616 |
| sentiment | v8          | baseline | tfidf-sgd    | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.539  |
| sentiment | v5          | baseline | tfidf-sgd    | ros          | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.4274 |
| sentiment | v8          | baseline | tfidf-svm    | class_weight | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6067 |
| sentiment | v5          | baseline | tfidf-svm    | class_weight | mono-fit | sinhala  | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6043 |
| sentiment | v8          | baseline | tfidf-svm    | none         | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6301 |
| sentiment | v8          | baseline | tfidf-svm    | ros          | mono-fit | sinhala  | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | sinhala  | 0.6024 |
| sentiment | v5          | encoder  | labse        | class_weight | mono-fit | sinhala  | train     | dev  |   43 | 6      | 32    | 2e-05 | n/a  | sinhala  | 0.6667 |
| intent    | same-labels | baseline | majority     | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8221 |
| intent    | same-labels | baseline | tfidf-knn    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8708 |
| intent    | same-labels | baseline | tfidf-logreg | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.918  |
| intent    | same-labels | baseline | tfidf-mnb    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9116 |
| intent    | same-labels | baseline | tfidf-rf     | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8832 |
| intent    | same-labels | baseline | tfidf-ridge  | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.885  |
| intent    | same-labels | baseline | tfidf-sgd    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9151 |
| intent    | same-labels | baseline | tfidf-svm    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9261 |
| priority  | same-labels | baseline | tfidf-knn    | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8925 |
| priority  | same-labels | baseline | tfidf-knn    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8925 |
| priority  | same-labels | baseline | tfidf-mnb    | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8664 |
| priority  | same-labels | baseline | tfidf-mnb    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8664 |
| priority  | same-labels | baseline | tfidf-rf     | ros          | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.8891 |
| priority  | same-labels | baseline | tfidf-ridge  | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.9092 |
| sentiment | v5          | baseline | majority     | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb    | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4926 |
| sentiment | v8          | baseline | tfidf-cnb    | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4926 |
| sentiment | v8          | baseline | tfidf-cnb    | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4467 |
| sentiment | v5          | baseline | tfidf-cnb    | ros          | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4444 |
| sentiment | v5          | baseline | tfidf-knn    | ros          | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4355 |
| sentiment | v8          | baseline | tfidf-logreg | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6091 |
| sentiment | v8          | baseline | tfidf-logreg | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.431  |
| sentiment | v8          | baseline | tfidf-logreg | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6146 |
| sentiment | v5          | baseline | tfidf-logreg | ros          | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6395 |
| sentiment | v5          | baseline | tfidf-mnb    | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5397 |
| sentiment | v5          | baseline | tfidf-mnb    | none         | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5397 |
| sentiment | v5          | baseline | tfidf-rf     | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.487  |
| sentiment | v5          | baseline | tfidf-ridge  | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.64   |
| sentiment | v8          | baseline | tfidf-sgd    | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5732 |
| sentiment | v8          | baseline | tfidf-sgd    | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5395 |
| sentiment | v8          | baseline | tfidf-sgd    | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5175 |
| sentiment | v5          | baseline | tfidf-sgd    | ros          | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.4202 |
| sentiment | v8          | baseline | tfidf-svm    | class_weight | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6087 |
| sentiment | v5          | baseline | tfidf-svm    | class_weight | mono-fit | singlish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.5839 |
| sentiment | v8          | baseline | tfidf-svm    | none         | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6389 |
| sentiment | v8          | baseline | tfidf-svm    | ros          | mono-fit | singlish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | singlish | 0.6036 |
| sentiment | v5          | encoder  | labse        | class_weight | mono-fit | singlish | train     | dev  |   43 | 6      | 32    | 2e-05 | n/a  | singlish | 0.6753 |
| intent    | same-labels | baseline | majority     | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8274 |
| intent    | same-labels | baseline | tfidf-knn    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8464 |
| intent    | same-labels | baseline | tfidf-logreg | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9095 |
| intent    | same-labels | baseline | tfidf-mnb    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9007 |
| intent    | same-labels | baseline | tfidf-rf     | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8823 |
| intent    | same-labels | baseline | tfidf-ridge  | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8845 |
| intent    | same-labels | baseline | tfidf-sgd    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9044 |
| intent    | same-labels | baseline | tfidf-svm    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.9156 |
| priority  | same-labels | baseline | tfidf-knn    | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.876  |
| priority  | same-labels | baseline | tfidf-knn    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.876  |
| priority  | same-labels | baseline | tfidf-mnb    | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8759 |
| priority  | same-labels | baseline | tfidf-mnb    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8759 |
| priority  | same-labels | baseline | tfidf-rf     | ros          | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8896 |
| priority  | same-labels | baseline | tfidf-ridge  | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.8972 |
| sentiment | v5          | baseline | majority     | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb    | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5    |
| sentiment | v8          | baseline | tfidf-cnb    | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5    |
| sentiment | v8          | baseline | tfidf-cnb    | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.4727 |
| sentiment | v5          | baseline | tfidf-cnb    | ros          | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.4569 |
| sentiment | v5          | baseline | tfidf-knn    | ros          | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.4183 |
| sentiment | v8          | baseline | tfidf-logreg | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6154 |
| sentiment | v8          | baseline | tfidf-logreg | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.4706 |
| sentiment | v8          | baseline | tfidf-logreg | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6492 |
| sentiment | v5          | baseline | tfidf-logreg | ros          | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5926 |
| sentiment | v5          | baseline | tfidf-mnb    | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5824 |
| sentiment | v5          | baseline | tfidf-mnb    | none         | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5824 |
| sentiment | v5          | baseline | tfidf-rf     | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.422  |
| sentiment | v5          | baseline | tfidf-ridge  | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6225 |
| sentiment | v8          | baseline | tfidf-sgd    | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6065 |
| sentiment | v8          | baseline | tfidf-sgd    | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5789 |
| sentiment | v8          | baseline | tfidf-sgd    | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.5517 |
| sentiment | v5          | baseline | tfidf-sgd    | ros          | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.4071 |
| sentiment | v8          | baseline | tfidf-svm    | class_weight | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6971 |
| sentiment | v5          | baseline | tfidf-svm    | class_weight | mono-fit | tamil    | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6074 |
| sentiment | v8          | baseline | tfidf-svm    | none         | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6443 |
| sentiment | v8          | baseline | tfidf-svm    | ros          | mono-fit | tamil    | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamil    | 0.6625 |
| sentiment | v5          | encoder  | labse        | class_weight | mono-fit | tamil    | train     | dev  |   43 | 6      | 32    | 2e-05 | n/a  | tamil    | 0.6763 |
| intent    | same-labels | baseline | majority     | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8357 |
| intent    | same-labels | baseline | tfidf-knn    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8763 |
| intent    | same-labels | baseline | tfidf-logreg | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9127 |
| intent    | same-labels | baseline | tfidf-mnb    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9292 |
| intent    | same-labels | baseline | tfidf-rf     | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8779 |
| intent    | same-labels | baseline | tfidf-ridge  | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.899  |
| intent    | same-labels | baseline | tfidf-sgd    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9187 |
| intent    | same-labels | baseline | tfidf-svm    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9233 |
| priority  | same-labels | baseline | tfidf-knn    | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8927 |
| priority  | same-labels | baseline | tfidf-knn    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8927 |
| priority  | same-labels | baseline | tfidf-mnb    | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8821 |
| priority  | same-labels | baseline | tfidf-mnb    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.8821 |
| priority  | same-labels | baseline | tfidf-rf     | ros          | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.888  |
| priority  | same-labels | baseline | tfidf-ridge  | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.9005 |
| sentiment | v5          | baseline | majority     | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb    | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5198 |
| sentiment | v8          | baseline | tfidf-cnb    | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5198 |
| sentiment | v8          | baseline | tfidf-cnb    | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.4412 |
| sentiment | v5          | baseline | tfidf-cnb    | ros          | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.4416 |
| sentiment | v5          | baseline | tfidf-knn    | ros          | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.4291 |
| sentiment | v8          | baseline | tfidf-logreg | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6176 |
| sentiment | v8          | baseline | tfidf-logreg | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.431  |
| sentiment | v8          | baseline | tfidf-logreg | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6054 |
| sentiment | v5          | baseline | tfidf-logreg | ros          | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5341 |
| sentiment | v5          | baseline | tfidf-mnb    | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5119 |
| sentiment | v5          | baseline | tfidf-mnb    | none         | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5119 |
| sentiment | v5          | baseline | tfidf-rf     | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.4717 |
| sentiment | v5          | baseline | tfidf-ridge  | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.589  |
| sentiment | v8          | baseline | tfidf-sgd    | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5478 |
| sentiment | v8          | baseline | tfidf-sgd    | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5175 |
| sentiment | v8          | baseline | tfidf-sgd    | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5068 |
| sentiment | v5          | baseline | tfidf-sgd    | ros          | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.4706 |
| sentiment | v8          | baseline | tfidf-svm    | class_weight | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.6265 |
| sentiment | v5          | baseline | tfidf-svm    | class_weight | mono-fit | tamilish | train     | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5735 |
| sentiment | v8          | baseline | tfidf-svm    | none         | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5674 |
| sentiment | v8          | baseline | tfidf-svm    | ros          | mono-fit | tamilish | unstamped | dev  |   42 | n/a    | n/a   | n/a   | n/a  | tamilish | 0.5828 |
| sentiment | v5          | encoder  | labse        | class_weight | mono-fit | tamilish | train     | dev  |   43 | 6      | 32    | 2e-05 | n/a  | tamilish | 0.5399 |

## Later dev — transfer training

| task      | labels      | family   | model                | arm          | regime       | train   | fit       | eval | seed | epochs | batch | lr  | LoRA | language | score  |
|:----------|:------------|:---------|:---------------------|:-------------|:-------------|:--------|:----------|:-----|-----:|:-------|:------|:----|:-----|:---------|:-------|
| intent    | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.537  |
| intent    | same-labels | baseline | tfidf-knn            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.581  |
| intent    | same-labels | baseline | tfidf-logreg         | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.6304 |
| intent    | same-labels | baseline | tfidf-mnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.6329 |
| intent    | same-labels | baseline | tfidf-rf             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.5447 |
| intent    | same-labels | baseline | tfidf-ridge          | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.5789 |
| intent    | same-labels | baseline | tfidf-sgd            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.6076 |
| intent    | same-labels | baseline | tfidf-svm            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.6262 |
| priority  | same-labels | baseline | intent-chained       | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.7066 |
| priority  | same-labels | baseline | intent-lookup-oracle | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.9147 |
| priority  | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.2302 |
| priority  | same-labels | baseline | tfidf-knn            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.7235 |
| priority  | same-labels | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.7525 |
| priority  | same-labels | baseline | tfidf-rf             | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.6559 |
| priority  | same-labels | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.7007 |
| sentiment | v5          | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.2338 |
| sentiment | v8          | baseline | tfidf-cnb            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.2338 |
| sentiment | v8          | baseline | tfidf-cnb            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.2494 |
| sentiment | v5          | baseline | tfidf-cnb            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1949 |
| sentiment | v5          | baseline | tfidf-knn            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.3077 |
| sentiment | v8          | baseline | tfidf-logreg         | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1333 |
| sentiment | v8          | baseline | tfidf-logreg         | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-logreg         | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1455 |
| sentiment | v5          | baseline | tfidf-logreg         | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.122  |
| sentiment | v5          | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.4154 |
| sentiment | v5          | baseline | tfidf-rf             | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v5          | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1728 |
| sentiment | v8          | baseline | tfidf-sgd            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v5          | baseline | tfidf-sgd            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.0    |
| sentiment | v8          | baseline | tfidf-svm            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1346 |
| sentiment | v5          | baseline | tfidf-svm            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1299 |
| sentiment | v8          | baseline | tfidf-svm            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.14   |
| sentiment | v8          | baseline | tfidf-svm            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | sinhala  | 0.1359 |
| intent    | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.5448 |
| intent    | same-labels | baseline | tfidf-knn            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.6077 |
| intent    | same-labels | baseline | tfidf-logreg         | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.6914 |
| intent    | same-labels | baseline | tfidf-mnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.7149 |
| intent    | same-labels | baseline | tfidf-rf             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.6448 |
| intent    | same-labels | baseline | tfidf-ridge          | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.5769 |
| intent    | same-labels | baseline | tfidf-sgd            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.6536 |
| intent    | same-labels | baseline | tfidf-svm            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.6618 |
| priority  | same-labels | baseline | intent-chained       | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.7467 |
| priority  | same-labels | baseline | intent-lookup-oracle | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.9147 |
| priority  | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.2302 |
| priority  | same-labels | baseline | tfidf-knn            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.7578 |
| priority  | same-labels | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.7596 |
| priority  | same-labels | baseline | tfidf-rf             | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.693  |
| priority  | same-labels | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.7166 |
| sentiment | v5          | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.2759 |
| sentiment | v8          | baseline | tfidf-cnb            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.2759 |
| sentiment | v8          | baseline | tfidf-cnb            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.2517 |
| sentiment | v5          | baseline | tfidf-cnb            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.3158 |
| sentiment | v5          | baseline | tfidf-knn            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.303  |
| sentiment | v8          | baseline | tfidf-logreg         | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.1224 |
| sentiment | v8          | baseline | tfidf-logreg         | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-logreg         | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.1031 |
| sentiment | v5          | baseline | tfidf-logreg         | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0822 |
| sentiment | v5          | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.3333 |
| sentiment | v5          | baseline | tfidf-rf             | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v5          | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.1519 |
| sentiment | v8          | baseline | tfidf-sgd            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v5          | baseline | tfidf-sgd            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0    |
| sentiment | v8          | baseline | tfidf-svm            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.1212 |
| sentiment | v5          | baseline | tfidf-svm            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.1096 |
| sentiment | v8          | baseline | tfidf-svm            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.044  |
| sentiment | v8          | baseline | tfidf-svm            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | singlish | 0.0825 |
| intent    | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0164 |
| intent    | same-labels | baseline | tfidf-knn            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0138 |
| intent    | same-labels | baseline | tfidf-logreg         | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0132 |
| intent    | same-labels | baseline | tfidf-mnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0166 |
| intent    | same-labels | baseline | tfidf-rf             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0127 |
| intent    | same-labels | baseline | tfidf-ridge          | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0178 |
| intent    | same-labels | baseline | tfidf-sgd            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0127 |
| intent    | same-labels | baseline | tfidf-svm            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0127 |
| priority  | same-labels | baseline | intent-chained       | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1802 |
| priority  | same-labels | baseline | intent-lookup-oracle | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.9147 |
| priority  | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.2302 |
| priority  | same-labels | baseline | tfidf-knn            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.2613 |
| priority  | same-labels | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.2724 |
| priority  | same-labels | baseline | tfidf-rf             | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.2341 |
| priority  | same-labels | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.2517 |
| sentiment | v5          | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1131 |
| sentiment | v8          | baseline | tfidf-cnb            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1131 |
| sentiment | v8          | baseline | tfidf-cnb            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1123 |
| sentiment | v5          | baseline | tfidf-cnb            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0871 |
| sentiment | v5          | baseline | tfidf-knn            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1538 |
| sentiment | v8          | baseline | tfidf-logreg         | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-logreg         | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-logreg         | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v5          | baseline | tfidf-logreg         | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v5          | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.1818 |
| sentiment | v5          | baseline | tfidf-rf             | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v5          | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.137  |
| sentiment | v8          | baseline | tfidf-sgd            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v5          | baseline | tfidf-sgd            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-svm            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0449 |
| sentiment | v5          | baseline | tfidf-svm            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0845 |
| sentiment | v8          | baseline | tfidf-svm            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0    |
| sentiment | v8          | baseline | tfidf-svm            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamil    | 0.0449 |
| intent    | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0005 |
| intent    | same-labels | baseline | tfidf-cnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.5094 |
| intent    | same-labels | baseline | tfidf-knn            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.5801 |
| intent    | same-labels | baseline | tfidf-logreg         | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6508 |
| intent    | same-labels | baseline | tfidf-mnb            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6503 |
| intent    | same-labels | baseline | tfidf-rf             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6031 |
| intent    | same-labels | baseline | tfidf-ridge          | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.547  |
| intent    | same-labels | baseline | tfidf-sgd            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.622  |
| intent    | same-labels | baseline | tfidf-svm            | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6323 |
| priority  | same-labels | baseline | intent-chained       | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.7509 |
| priority  | same-labels | baseline | intent-lookup-oracle | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.9147 |
| priority  | same-labels | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.2302 |
| priority  | same-labels | baseline | tfidf-knn            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.7169 |
| priority  | same-labels | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.7391 |
| priority  | same-labels | baseline | tfidf-rf             | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6831 |
| priority  | same-labels | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.6939 |
| sentiment | v5          | baseline | majority             | none         | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-cnb            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.2489 |
| sentiment | v8          | baseline | tfidf-cnb            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.2489 |
| sentiment | v8          | baseline | tfidf-cnb            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.3125 |
| sentiment | v5          | baseline | tfidf-cnb            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.284  |
| sentiment | v5          | baseline | tfidf-knn            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.2903 |
| sentiment | v8          | baseline | tfidf-logreg         | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.16   |
| sentiment | v8          | baseline | tfidf-logreg         | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-logreg         | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.125  |
| sentiment | v5          | baseline | tfidf-logreg         | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.08   |
| sentiment | v5          | baseline | tfidf-mnb            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.2963 |
| sentiment | v5          | baseline | tfidf-rf             | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0282 |
| sentiment | v5          | baseline | tfidf-ridge          | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.1538 |
| sentiment | v8          | baseline | tfidf-sgd            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-sgd            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v5          | baseline | tfidf-sgd            | ros          | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0    |
| sentiment | v8          | baseline | tfidf-svm            | class_weight | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.1053 |
| sentiment | v5          | baseline | tfidf-svm            | class_weight | transfer-fit | english | train     | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0833 |
| sentiment | v8          | baseline | tfidf-svm            | none         | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.0444 |
| sentiment | v8          | baseline | tfidf-svm            | ros          | transfer-fit | english | unstamped | dev  |   42 | n/a    | n/a   | n/a | n/a  | tamilish | 0.086  |

## Later test — pooled training

| task      | labels      | family            | model                            | arm          | regime     | train                                   | fit                         | eval | seed | epochs | batch | lr     | LoRA | all    | english | sinhala | singlish | tamil  | tamilish |
|:----------|:------------|:------------------|:---------------------------------|:-------------|:-----------|:----------------------------------------|:----------------------------|:-----|-----:|:-------|:------|:-------|:-----|:-------|:--------|:--------|:---------|:-------|:---------|
| intent    | same-labels | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.0003 | 0.0003  | 0.0003  | 0.0003   | 0.0003 | 0.0003   |
| intent    | same-labels | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6792 | 0.7772  | 0.6732  | 0.7194   | 0.7234 | 0.4925   |
| intent    | same-labels | baseline          | tfidf-knn                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.7332 | 0.8345  | 0.7687  | 0.7768   | 0.749  | 0.5149   |
| intent    | same-labels | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8189 | 0.9096  | 0.8595  | 0.8751   | 0.8302 | 0.5854   |
| intent    | same-labels | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8052 | 0.8853  | 0.8469  | 0.858    | 0.8294 | 0.582    |
| intent    | same-labels | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.7946 | 0.878   | 0.8312  | 0.8529   | 0.8102 | 0.5604   |
| intent    | same-labels | baseline          | tfidf-ridge                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.7653 | 0.8589  | 0.7952  | 0.8139   | 0.7779 | 0.5522   |
| intent    | same-labels | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8115 | 0.9079  | 0.8489  | 0.8646   | 0.8305 | 0.5669   |
| intent    | same-labels | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | unstamped                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8307 | —       | —       | —        | —      | —        |
| intent    | same-labels | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8308 | 0.918   | 0.8666  | 0.8793   | 0.8528 | 0.6127   |
| intent    | same-labels | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 8     | 0.0001 | all  | 0.8635 | —       | —       | —        | —      | —        |
| intent    | same-labels | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 8     | 0.0001 | n/a  | —      | 0.9358  | 0.9221  | 0.8962   | 0.911  | 0.6281   |
| intent    | same-labels | decoder           | gemma-3-270m                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 8     | 0.0001 | all  | 0.8414 | —       | —       | —        | —      | —        |
| intent    | same-labels | decoder           | gemma-3-270m                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 8     | 0.0001 | n/a  | —      | 0.9288  | 0.8874  | 0.8706   | 0.8907 | 0.6041   |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.8616 | —       | —       | —        | —      | —        |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.8673 | —       | —       | —        | —      | —        |
| intent    | same-labels | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.8835 | 0.9412  | 0.9319  | 0.9034   | 0.9329 | 0.6928   |
| intent    | same-labels | encoder           | mmbert                           | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.868  | 0.9374  | 0.9123  | 0.9013   | 0.9147 | 0.6566   |
| intent    | same-labels | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.8467 | 0.9226  | 0.7224  | 0.8888   | 0.908  | 0.7824   |
| intent    | same-labels | encoder           | xlmr-base                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.8801 | 0.9402  | 0.9244  | 0.8987   | 0.9151 | 0.7067   |
| priority  | same-labels | baseline          | intent-chained                   | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8557 | 0.8855  | 0.8699  | 0.8741   | 0.8648 | 0.7846   |
| priority  | same-labels | baseline          | intent-lookup-oracle             | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.9051 | 0.9051  | 0.9051  | 0.9051   | 0.9051 | 0.9051   |
| priority  | same-labels | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.2361 | 0.2361  | 0.2361  | 0.2361   | 0.2361 | 0.2361   |
| priority  | same-labels | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8422 | 0.8643  | 0.8479  | 0.854    | 0.8653 | 0.7782   |
| priority  | same-labels | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8422 | 0.8643  | 0.8479  | 0.854    | 0.8653 | 0.7782   |
| priority  | same-labels | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8269 | 0.8613  | 0.8326  | 0.8392   | 0.8475 | 0.7533   |
| priority  | same-labels | baseline          | tfidf-knn                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8379 | 0.8803  | 0.8541  | 0.8594   | 0.8561 | 0.7306   |
| priority  | same-labels | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8689 | 0.8915  | 0.8826  | 0.8837   | 0.8857 | 0.8015   |
| priority  | same-labels | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8677 | 0.8974  | 0.8768  | 0.883    | 0.8831 | 0.7925   |
| priority  | same-labels | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8706 | 0.8987  | 0.881   | 0.8889   | 0.8849 | 0.7985   |
| priority  | same-labels | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8452 | 0.8724  | 0.8539  | 0.863    | 0.8634 | 0.7754   |
| priority  | same-labels | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.858  | 0.8864  | 0.8575  | 0.879    | 0.8787 | 0.7849   |
| priority  | same-labels | baseline          | tfidf-ridge                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8754 | 0.9002  | 0.8868  | 0.894    | 0.8958 | 0.7986   |
| priority  | same-labels | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8603 | 0.891   | 0.872   | 0.8781   | 0.8775 | 0.7798   |
| priority  | same-labels | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8631 | 0.8932  | 0.877   | 0.8801   | 0.881  | 0.7818   |
| priority  | same-labels | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8659 | 0.8953  | 0.8802  | 0.8831   | 0.8853 | 0.7805   |
| priority  | same-labels | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8734 | 0.905   | 0.8848  | 0.8918   | 0.8854 | 0.7984   |
| priority  | same-labels | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8716 | 0.9007  | 0.8854  | 0.8873   | 0.8863 | 0.7962   |
| priority  | same-labels | baseline          | tfidf-svm                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8683 | 0.8988  | 0.8781  | 0.8886   | 0.8876 | 0.7842   |
| priority  | same-labels | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.8898 | —       | —       | —        | —      | —        |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.8895 | —       | —       | —        | —      | —        |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.8904 | —       | —       | —        | —      | —        |
| priority  | same-labels | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev-posterior-rescore | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.8901 | 0.9229  | 0.9179  | 0.8817   | 0.913  | 0.8142   |
| priority  | same-labels | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.8717 | 0.9095  | 0.8072  | 0.8861   | 0.912  | 0.8412   |
| sentiment | v5          | baseline          | majority                         | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.0    | 0.0     | 0.0     | 0.0      | 0.0    | 0.0      |
| sentiment | v8          | baseline          | tfidf-cnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4827 | 0.5255  | 0.4984  | 0.5521   | 0.4716 | 0.3985   |
| sentiment | v8          | baseline          | tfidf-cnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4827 | 0.5255  | 0.4984  | 0.5521   | 0.4716 | 0.3985   |
| sentiment | v8          | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4968 | 0.5139  | 0.5083  | 0.5302   | 0.5239 | 0.3738   |
| sentiment | v5          | baseline          | tfidf-cnb                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.3355 | 0.3321  | 0.3311  | 0.3433   | 0.3561 | 0.3097   |
| sentiment | v8          | baseline          | tfidf-knn                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4808 | 0.5196  | 0.4824  | 0.4932   | 0.5135 | 0.3755   |
| sentiment | v5          | baseline          | tfidf-knn                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.3209 | 0.3325  | 0.3234  | 0.3333   | 0.3532 | 0.2492   |
| sentiment | v8          | baseline          | tfidf-logreg                     | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6286 | 0.6793  | 0.5992  | 0.6157   | 0.661  | 0.5874   |
| sentiment | v8          | baseline          | tfidf-logreg                     | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4279 | 0.4891  | 0.4341  | 0.5055   | 0.4521 | 0.2232   |
| sentiment | v8          | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6383 | 0.6995  | 0.6256  | 0.6545   | 0.6776 | 0.5074   |
| sentiment | v5          | baseline          | tfidf-logreg                     | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4449 | 0.4698  | 0.4467  | 0.457    | 0.4746 | 0.3431   |
| sentiment | v5          | baseline          | tfidf-mnb                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4137 | 0.4211  | 0.4087  | 0.4389   | 0.415  | 0.3862   |
| sentiment | v8          | baseline          | tfidf-mnb                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.5824 | 0.6059  | 0.5865  | 0.6123   | 0.6004 | 0.4878   |
| sentiment | v8          | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.5492 | 0.5956  | 0.5845  | 0.5732   | 0.5871 | 0.3692   |
| sentiment | v5          | baseline          | tfidf-rf                         | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.3578 | 0.4045  | 0.3616  | 0.358    | 0.4142 | 0.2154   |
| sentiment | v5          | baseline          | tfidf-ridge                      | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4563 | 0.4579  | 0.4373  | 0.4642   | 0.5101 | 0.4033   |
| sentiment | v8          | baseline          | tfidf-ridge                      | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.5354 | 0.6246  | 0.4855  | 0.5436   | 0.6067 | 0.3871   |
| sentiment | v8          | baseline          | tfidf-sgd                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6008 | 0.6304  | 0.5866  | 0.6166   | 0.6776 | 0.48     |
| sentiment | v8          | baseline          | tfidf-sgd                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6075 | 0.6667  | 0.6126  | 0.61     | 0.6437 | 0.4984   |
| sentiment | v8          | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6092 | 0.6842  | 0.5954  | 0.6218   | 0.6608 | 0.4577   |
| sentiment | v5          | baseline          | tfidf-sgd                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.3988 | 0.4455  | 0.3269  | 0.3654   | 0.5149 | 0.327    |
| sentiment | v8          | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6653 | 0.7198  | 0.6412  | 0.6633   | 0.7249 | 0.5722   |
| sentiment | v5          | baseline          | tfidf-svm                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.4562 | 0.4444  | 0.4203  | 0.4604   | 0.5338 | 0.4163   |
| sentiment | v8          | baseline          | tfidf-svm                        | none         | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6161 | 0.6646  | 0.613   | 0.6335   | 0.6395 | 0.5208   |
| sentiment | v8          | baseline          | tfidf-svm                        | ros          | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | n/a    | n/a   | n/a    | n/a  | 0.6047 | 0.6839  | 0.5994  | 0.6106   | 0.6512 | 0.4558   |
| sentiment | v8          | decoder           | gemma-3-1b                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.7126 | —       | —       | —        | —      | —        |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-shared3head | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.7042 | —       | —       | —        | —      | —        |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-sharedhead  | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 16    | 0.0001 | all  | 0.7048 | —       | —       | —        | —      | —        |
| sentiment | v8          | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 3      | 32    | 2e-05  | n/a  | 0.7138 | 0.8032  | 0.7234  | 0.6757   | 0.7606 | 0.5948   |
| sentiment | v8          | encoder           | labse                            | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   43 | 6      | 32    | 2e-05  | n/a  | 0.6963 | 0.755   | 0.7139  | 0.6402   | 0.7535 | 0.6185   |
| sentiment | v8          | encoder           | mmbert                           | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.7    | 0.7723  | 0.6766  | 0.6905   | 0.7386 | 0.6159   |
| sentiment | v8          | encoder           | muril-base                       | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.679  | 0.7967  | 0.5577  | 0.6463   | 0.7465 | 0.6235   |
| sentiment | v8          | encoder           | xlmr-base                        | class_weight | pooled-fit | english,sinhala,singlish,tamil,tamilish | train+dev                   | test |   42 | 6      | 32    | 2e-05  | n/a  | 0.7007 | 0.7838  | 0.7215  | 0.6361   | 0.7473 | 0.5981   |

## V5 sentiment baselines — pooled-fit dev

| model        | arm          | train                                   | fit   |    all | english | sinhala | singlish | tamil  | tamilish |
|:-------------|:-------------|:----------------------------------------|:------|-------:|:--------|:--------|:---------|:-------|:---------|
| majority     | none         | english,sinhala,singlish,tamil,tamilish | train |    0.0 | 0.0     | 0.0     | 0.0      | 0.0    | 0.0      |
| tfidf-cnb    | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.4281 | 0.4409  | 0.4409  | 0.5246   | 0.3609 | 0.4226   |
| tfidf-cnb    | none         | english,sinhala,singlish,tamil,tamilish | train | 0.4281 | 0.4409  | 0.4409  | 0.5246   | 0.3609 | 0.4226   |
| tfidf-cnb    | ros          | english,sinhala,singlish,tamil,tamilish | train |  0.442 | 0.428   | 0.4385  | 0.475    | 0.4331 | 0.438    |
| tfidf-knn    | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.1499 | 0.1818  | 0.175   | 0.1538   | 0.08   | 0.1558   |
| tfidf-knn    | none         | english,sinhala,singlish,tamil,tamilish | train | 0.1499 | 0.1818  | 0.175   | 0.1538   | 0.08   | 0.1558   |
| tfidf-knn    | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.4487 | 0.4622  | 0.453   | 0.4268   | 0.4444 | 0.4581   |
| tfidf-logreg | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.5742 | 0.5969  | 0.5914  | 0.5926   | 0.5445 | 0.5455   |
| tfidf-logreg | none         | english,sinhala,singlish,tamil,tamilish | train | 0.2676 | 0.3133  | 0.2278  | 0.3256   | 0.241  | 0.225    |
| tfidf-logreg | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.5854 | 0.5476  | 0.5882  | 0.6303   | 0.5854 | 0.5752   |
| tfidf-mnb    | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.5297 | 0.4851  | 0.5455  | 0.5783   | 0.514  | 0.5368   |
| tfidf-mnb    | none         | english,sinhala,singlish,tamil,tamilish | train | 0.5297 | 0.4851  | 0.5455  | 0.5783   | 0.514  | 0.5368   |
| tfidf-mnb    | ros          | english,sinhala,singlish,tamil,tamilish | train |   0.45 | 0.4215  | 0.4667  | 0.4762   | 0.4463 | 0.4426   |
| tfidf-rf     | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.4559 | 0.4444  | 0.4587  | 0.4528   | 0.4602 | 0.463    |
| tfidf-rf     | none         | english,sinhala,singlish,tamil,tamilish | train | 0.2632 | 0.2683  | 0.3059  | 0.2892   | 0.2093 | 0.2439   |
| tfidf-rf     | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.2597 | 0.1905  | 0.3111  | 0.3441   | 0.1667 | 0.2727   |
| tfidf-ridge  | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.6109 | 0.6049  | 0.625   | 0.6203   | 0.6234 | 0.5806   |
| tfidf-ridge  | none         | english,sinhala,singlish,tamil,tamilish | train | 0.3728 | 0.3297  | 0.3736  | 0.4348   | 0.3333 | 0.3913   |
| tfidf-ridge  | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.5794 | 0.576   | 0.6131  | 0.6029   | 0.5528 | 0.5469   |
| tfidf-sgd    | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.5282 | 0.544   | 0.5     | 0.5278   | 0.5231 | 0.5484   |
| tfidf-sgd    | none         | english,sinhala,singlish,tamil,tamilish | train | 0.5087 | 0.531   | 0.4602  | 0.4909   | 0.521  | 0.5378   |
| tfidf-sgd    | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.5333 | 0.5714  | 0.5574  | 0.562    | 0.4727 | 0.4956   |
| tfidf-svm    | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.5901 | 0.6069  | 0.5915  | 0.6187   | 0.6087 | 0.5248   |
| tfidf-svm    | none         | english,sinhala,singlish,tamil,tamilish | train | 0.4944 | 0.5273  | 0.4906  | 0.4673   | 0.4952 | 0.4906   |
| tfidf-svm    | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.5195 | 0.5405  | 0.5714  | 0.5556   | 0.4643 | 0.4561   |

## V5 sentiment baselines — pooled-fit test

| model        | arm          | train                                   | fit       | all    | english | sinhala | singlish | tamil  | tamilish |
|:-------------|:-------------|:----------------------------------------|:----------|:-------|:--------|:--------|:---------|:-------|:---------|
| majority     | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.0    | 0.0     | 0.0     | 0.0      | 0.0    | 0.0      |
| tfidf-cnb    | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.3355 | 0.3321  | 0.3311  | 0.3433   | 0.3561 | 0.3097   |
| tfidf-knn    | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.3209 | 0.3325  | 0.3234  | 0.3333   | 0.3532 | 0.2492   |
| tfidf-logreg | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.4449 | 0.4698  | 0.4467  | 0.457    | 0.4746 | 0.3431   |
| tfidf-mnb    | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.4137 | 0.4211  | 0.4087  | 0.4389   | 0.415  | 0.3862   |
| tfidf-rf     | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.3578 | 0.4045  | 0.3616  | 0.358    | 0.4142 | 0.2154   |
| tfidf-ridge  | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.4563 | 0.4579  | 0.4373  | 0.4642   | 0.5101 | 0.4033   |
| tfidf-sgd    | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.3988 | 0.4455  | 0.3269  | 0.3654   | 0.5149 | 0.327    |
| tfidf-svm    | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.4562 | 0.4444  | 0.4203  | 0.4604   | 0.5338 | 0.4163   |

## V5 sentiment baselines — mono-fit dev

| model        | arm          | train    | fit   | language | score  |
|:-------------|:-------------|:---------|:------|:---------|:-------|
| majority     | none         | english  | train | english  | 0.0    |
| tfidf-cnb    | ros          | english  | train | english  | 0.4113 |
| tfidf-knn    | ros          | english  | train | english  | 0.4508 |
| tfidf-logreg | ros          | english  | train | english  | 0.5698 |
| tfidf-mnb    | class_weight | english  | train | english  | 0.5567 |
| tfidf-mnb    | none         | english  | train | english  | 0.5567 |
| tfidf-rf     | class_weight | english  | train | english  | 0.4815 |
| tfidf-ridge  | class_weight | english  | train | english  | 0.5844 |
| tfidf-sgd    | ros          | english  | train | english  | 0.3429 |
| tfidf-svm    | class_weight | english  | train | english  | 0.6015 |
| majority     | none         | sinhala  | train | sinhala  | 0.0    |
| tfidf-cnb    | ros          | sinhala  | train | sinhala  | 0.4392 |
| tfidf-knn    | ros          | sinhala  | train | sinhala  | 0.4372 |
| tfidf-logreg | ros          | sinhala  | train | sinhala  | 0.6353 |
| tfidf-mnb    | class_weight | sinhala  | train | sinhala  | 0.5155 |
| tfidf-mnb    | none         | sinhala  | train | sinhala  | 0.5155 |
| tfidf-rf     | class_weight | sinhala  | train | sinhala  | 0.5043 |
| tfidf-ridge  | class_weight | sinhala  | train | sinhala  | 0.6316 |
| tfidf-sgd    | ros          | sinhala  | train | sinhala  | 0.4274 |
| tfidf-svm    | class_weight | sinhala  | train | sinhala  | 0.6043 |
| majority     | none         | singlish | train | singlish | 0.0    |
| tfidf-cnb    | ros          | singlish | train | singlish | 0.4444 |
| tfidf-knn    | ros          | singlish | train | singlish | 0.4355 |
| tfidf-logreg | ros          | singlish | train | singlish | 0.6395 |
| tfidf-mnb    | class_weight | singlish | train | singlish | 0.5397 |
| tfidf-mnb    | none         | singlish | train | singlish | 0.5397 |
| tfidf-rf     | class_weight | singlish | train | singlish | 0.487  |
| tfidf-ridge  | class_weight | singlish | train | singlish | 0.64   |
| tfidf-sgd    | ros          | singlish | train | singlish | 0.4202 |
| tfidf-svm    | class_weight | singlish | train | singlish | 0.5839 |
| majority     | none         | tamil    | train | tamil    | 0.0    |
| tfidf-cnb    | ros          | tamil    | train | tamil    | 0.4569 |
| tfidf-knn    | ros          | tamil    | train | tamil    | 0.4183 |
| tfidf-logreg | ros          | tamil    | train | tamil    | 0.5926 |
| tfidf-mnb    | class_weight | tamil    | train | tamil    | 0.5824 |
| tfidf-mnb    | none         | tamil    | train | tamil    | 0.5824 |
| tfidf-rf     | class_weight | tamil    | train | tamil    | 0.422  |
| tfidf-ridge  | class_weight | tamil    | train | tamil    | 0.6225 |
| tfidf-sgd    | ros          | tamil    | train | tamil    | 0.4071 |
| tfidf-svm    | class_weight | tamil    | train | tamil    | 0.6074 |
| majority     | none         | tamilish | train | tamilish | 0.0    |
| tfidf-cnb    | ros          | tamilish | train | tamilish | 0.4416 |
| tfidf-knn    | ros          | tamilish | train | tamilish | 0.4291 |
| tfidf-logreg | ros          | tamilish | train | tamilish | 0.5341 |
| tfidf-mnb    | class_weight | tamilish | train | tamilish | 0.5119 |
| tfidf-mnb    | none         | tamilish | train | tamilish | 0.5119 |
| tfidf-rf     | class_weight | tamilish | train | tamilish | 0.4717 |
| tfidf-ridge  | class_weight | tamilish | train | tamilish | 0.589  |
| tfidf-sgd    | ros          | tamilish | train | tamilish | 0.4706 |
| tfidf-svm    | class_weight | tamilish | train | tamilish | 0.5735 |

## V5 sentiment baselines — mono-fit test

| model        | arm          | train    | fit       | language | score  |
|:-------------|:-------------|:---------|:----------|:---------|:-------|
| majority     | none         | english  | train+dev | english  | 0.0    |
| tfidf-cnb    | ros          | english  | train+dev | english  | 0.3482 |
| tfidf-knn    | ros          | english  | train+dev | english  | 0.3302 |
| tfidf-logreg | ros          | english  | train+dev | english  | 0.4539 |
| tfidf-mnb    | class_weight | english  | train+dev | english  | 0.4286 |
| tfidf-rf     | class_weight | english  | train+dev | english  | 0.3765 |
| tfidf-ridge  | class_weight | english  | train+dev | english  | 0.4366 |
| tfidf-sgd    | ros          | english  | train+dev | english  | 0.4043 |
| tfidf-svm    | class_weight | english  | train+dev | english  | 0.4498 |
| majority     | none         | sinhala  | train+dev | sinhala  | 0.0    |
| tfidf-cnb    | ros          | sinhala  | train+dev | sinhala  | 0.3209 |
| tfidf-knn    | ros          | sinhala  | train+dev | sinhala  | 0.2907 |
| tfidf-logreg | ros          | sinhala  | train+dev | sinhala  | 0.4383 |
| tfidf-mnb    | class_weight | sinhala  | train+dev | sinhala  | 0.39   |
| tfidf-rf     | class_weight | sinhala  | train+dev | sinhala  | 0.3617 |
| tfidf-ridge  | class_weight | sinhala  | train+dev | sinhala  | 0.4518 |
| tfidf-sgd    | ros          | sinhala  | train+dev | sinhala  | 0.3545 |
| tfidf-svm    | class_weight | sinhala  | train+dev | sinhala  | 0.4229 |
| majority     | none         | singlish | train+dev | singlish | 0.0    |
| tfidf-cnb    | ros          | singlish | train+dev | singlish | 0.334  |
| tfidf-knn    | ros          | singlish | train+dev | singlish | 0.3108 |
| tfidf-logreg | ros          | singlish | train+dev | singlish | 0.4562 |
| tfidf-mnb    | class_weight | singlish | train+dev | singlish | 0.4043 |
| tfidf-rf     | class_weight | singlish | train+dev | singlish | 0.3626 |
| tfidf-ridge  | class_weight | singlish | train+dev | singlish | 0.4842 |
| tfidf-sgd    | ros          | singlish | train+dev | singlish | 0.3509 |
| tfidf-svm    | class_weight | singlish | train+dev | singlish | 0.4672 |
| majority     | none         | tamil    | train+dev | tamil    | 0.0    |
| tfidf-cnb    | ros          | tamil    | train+dev | tamil    | 0.3801 |
| tfidf-knn    | ros          | tamil    | train+dev | tamil    | 0.3387 |
| tfidf-logreg | ros          | tamil    | train+dev | tamil    | 0.4863 |
| tfidf-mnb    | class_weight | tamil    | train+dev | tamil    | 0.478  |
| tfidf-rf     | class_weight | tamil    | train+dev | tamil    | 0.4    |
| tfidf-ridge  | class_weight | tamil    | train+dev | tamil    | 0.5226 |
| tfidf-sgd    | ros          | tamil    | train+dev | tamil    | 0.495  |
| tfidf-svm    | class_weight | tamil    | train+dev | tamil    | 0.5339 |
| majority     | none         | tamilish | train+dev | tamilish | 0.0    |
| tfidf-cnb    | ros          | tamilish | train+dev | tamilish | 0.2857 |
| tfidf-knn    | ros          | tamilish | train+dev | tamilish | 0.2626 |
| tfidf-logreg | ros          | tamilish | train+dev | tamilish | 0.4018 |
| tfidf-mnb    | class_weight | tamilish | train+dev | tamilish | 0.4    |
| tfidf-rf     | class_weight | tamilish | train+dev | tamilish | 0.2362 |
| tfidf-ridge  | class_weight | tamilish | train+dev | tamilish | 0.434  |
| tfidf-sgd    | ros          | tamilish | train+dev | tamilish | 0.2628 |
| tfidf-svm    | class_weight | tamilish | train+dev | tamilish | 0.4369 |

## V5 sentiment baselines — transfer-fit dev

| model        | arm          | train   | fit   | language | score  |
|:-------------|:-------------|:--------|:------|:---------|:-------|
| majority     | none         | english | train | sinhala  | 0.0    |
| tfidf-cnb    | ros          | english | train | sinhala  | 0.1949 |
| tfidf-knn    | ros          | english | train | sinhala  | 0.3077 |
| tfidf-logreg | ros          | english | train | sinhala  | 0.122  |
| tfidf-mnb    | class_weight | english | train | sinhala  | 0.4154 |
| tfidf-rf     | class_weight | english | train | sinhala  | 0.0    |
| tfidf-ridge  | class_weight | english | train | sinhala  | 0.1728 |
| tfidf-sgd    | ros          | english | train | sinhala  | 0.0    |
| tfidf-svm    | class_weight | english | train | sinhala  | 0.1299 |
| majority     | none         | english | train | singlish | 0.0    |
| tfidf-cnb    | ros          | english | train | singlish | 0.3158 |
| tfidf-knn    | ros          | english | train | singlish | 0.303  |
| tfidf-logreg | ros          | english | train | singlish | 0.0822 |
| tfidf-mnb    | class_weight | english | train | singlish | 0.3333 |
| tfidf-rf     | class_weight | english | train | singlish | 0.0    |
| tfidf-ridge  | class_weight | english | train | singlish | 0.1519 |
| tfidf-sgd    | ros          | english | train | singlish | 0.0    |
| tfidf-svm    | class_weight | english | train | singlish | 0.1096 |
| majority     | none         | english | train | tamil    | 0.0    |
| tfidf-cnb    | ros          | english | train | tamil    | 0.0871 |
| tfidf-knn    | ros          | english | train | tamil    | 0.1538 |
| tfidf-logreg | ros          | english | train | tamil    | 0.0    |
| tfidf-mnb    | class_weight | english | train | tamil    | 0.1818 |
| tfidf-rf     | class_weight | english | train | tamil    | 0.0    |
| tfidf-ridge  | class_weight | english | train | tamil    | 0.137  |
| tfidf-sgd    | ros          | english | train | tamil    | 0.0    |
| tfidf-svm    | class_weight | english | train | tamil    | 0.0845 |
| majority     | none         | english | train | tamilish | 0.0    |
| tfidf-cnb    | ros          | english | train | tamilish | 0.284  |
| tfidf-knn    | ros          | english | train | tamilish | 0.2903 |
| tfidf-logreg | ros          | english | train | tamilish | 0.08   |
| tfidf-mnb    | class_weight | english | train | tamilish | 0.2963 |
| tfidf-rf     | class_weight | english | train | tamilish | 0.0282 |
| tfidf-ridge  | class_weight | english | train | tamilish | 0.1538 |
| tfidf-sgd    | ros          | english | train | tamilish | 0.0    |
| tfidf-svm    | class_weight | english | train | tamilish | 0.0833 |

## V5 sentiment baselines — transfer-fit test

| model        | arm          | train   | fit       | language | score  |
|:-------------|:-------------|:--------|:----------|:---------|:-------|
| majority     | none         | english | train+dev | sinhala  | 0.0    |
| tfidf-cnb    | ros          | english | train+dev | sinhala  | 0.1414 |
| tfidf-knn    | ros          | english | train+dev | sinhala  | 0.1655 |
| tfidf-logreg | ros          | english | train+dev | sinhala  | 0.1562 |
| tfidf-mnb    | class_weight | english | train+dev | sinhala  | 0.25   |
| tfidf-rf     | class_weight | english | train+dev | sinhala  | 0.0192 |
| tfidf-ridge  | class_weight | english | train+dev | sinhala  | 0.1301 |
| tfidf-sgd    | ros          | english | train+dev | sinhala  | 0.0    |
| tfidf-svm    | class_weight | english | train+dev | sinhala  | 0.0522 |
| majority     | none         | english | train+dev | singlish | 0.0    |
| tfidf-cnb    | ros          | english | train+dev | singlish | 0.2126 |
| tfidf-knn    | ros          | english | train+dev | singlish | 0.1695 |
| tfidf-logreg | ros          | english | train+dev | singlish | 0.0545 |
| tfidf-mnb    | class_weight | english | train+dev | singlish | 0.2678 |
| tfidf-rf     | class_weight | english | train+dev | singlish | 0.0566 |
| tfidf-ridge  | class_weight | english | train+dev | singlish | 0.1167 |
| tfidf-sgd    | ros          | english | train+dev | singlish | 0.0    |
| tfidf-svm    | class_weight | english | train+dev | singlish | 0.0721 |
| majority     | none         | english | train+dev | tamil    | 0.0    |
| tfidf-cnb    | ros          | english | train+dev | tamil    | 0.0636 |
| tfidf-knn    | ros          | english | train+dev | tamil    | 0.1818 |
| tfidf-logreg | ros          | english | train+dev | tamil    | 0.0    |
| tfidf-mnb    | class_weight | english | train+dev | tamil    | 0.1391 |
| tfidf-rf     | class_weight | english | train+dev | tamil    | 0.0    |
| tfidf-ridge  | class_weight | english | train+dev | tamil    | 0.1111 |
| tfidf-sgd    | ros          | english | train+dev | tamil    | 0.0    |
| tfidf-svm    | class_weight | english | train+dev | tamil    | 0.0577 |
| majority     | none         | english | train+dev | tamilish | 0.0    |
| tfidf-cnb    | ros          | english | train+dev | tamilish | 0.1216 |
| tfidf-knn    | ros          | english | train+dev | tamilish | 0.1114 |
| tfidf-logreg | ros          | english | train+dev | tamilish | 0.0    |
| tfidf-mnb    | class_weight | english | train+dev | tamilish | 0.2286 |
| tfidf-rf     | class_weight | english | train+dev | tamilish | 0.0    |
| tfidf-ridge  | class_weight | english | train+dev | tamilish | 0.0541 |
| tfidf-sgd    | ros          | english | train+dev | tamilish | 0.0    |
| tfidf-svm    | class_weight | english | train+dev | tamilish | 0.0377 |

## Intent baselines — pooled-fit dev

| era   | model        | arm          | train                                   | fit       |    all | english | sinhala | singlish | tamil  | tamilish |
|:------|:-------------|:-------------|:----------------------------------------|:----------|-------:|:--------|:--------|:---------|:-------|:---------|
| later | majority     | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.0005 | 0.0005  | 0.0005  | 0.0005   | 0.0005 | 0.0005   |
| later | tfidf-cnb    | class_weight | english,sinhala,singlish,tamil,tamilish | unstamped | 0.8048 | —       | —       | —        | —      | —        |
| later | tfidf-cnb    | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.8048 | 0.7703  | 0.7972  | 0.8035   | 0.8167 | 0.8291   |
| later | tfidf-knn    | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.8412 | 0.8152  | 0.8506  | 0.8506   | 0.8359 | 0.8534   |
| later | tfidf-logreg | class_weight | english,sinhala,singlish,tamil,tamilish | unstamped | 0.9104 | —       | —       | —        | —      | —        |
| later | tfidf-logreg | none         | english,sinhala,singlish,tamil,tamilish | train     |  0.912 | 0.8922  | 0.9181  | 0.9181   | 0.9127 | 0.9188   |
| later | tfidf-mnb    | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.9062 | 0.8864  | 0.9135  | 0.907    | 0.897  | 0.9268   |
| later | tfidf-rf     | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.8788 | 0.8629  | 0.878   | 0.8843   | 0.884  | 0.8852   |
| later | tfidf-ridge  | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.8775 | 0.8563  | 0.8851  | 0.8718   | 0.8817 | 0.8906   |
| later | tfidf-sgd    | class_weight | english,sinhala,singlish,tamil,tamilish | unstamped |  0.905 | —       | —       | —        | —      | —        |
| later | tfidf-sgd    | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.9092 | 0.8939  | 0.9145  | 0.908    | 0.9034 | 0.9266   |
| later | tfidf-svm    | class_weight | english,sinhala,singlish,tamil,tamilish | unstamped | 0.9201 | —       | —       | —        | —      | —        |
| later | tfidf-svm    | none         | english,sinhala,singlish,tamil,tamilish | train     | 0.9202 | 0.9068  | 0.9258  | 0.9252   | 0.9155 | 0.9288   |

## Intent baselines — pooled-fit test

| era   | model        | arm          | train                                   | fit       | all    | english | sinhala | singlish | tamil  | tamilish |
|:------|:-------------|:-------------|:----------------------------------------|:----------|:-------|:--------|:--------|:---------|:-------|:---------|
| later | majority     | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.0003 | 0.0003  | 0.0003  | 0.0003   | 0.0003 | 0.0003   |
| later | tfidf-cnb    | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.6792 | 0.7772  | 0.6732  | 0.7194   | 0.7234 | 0.4925   |
| later | tfidf-knn    | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.7332 | 0.8345  | 0.7687  | 0.7768   | 0.749  | 0.5149   |
| later | tfidf-logreg | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8189 | 0.9096  | 0.8595  | 0.8751   | 0.8302 | 0.5854   |
| later | tfidf-mnb    | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8052 | 0.8853  | 0.8469  | 0.858    | 0.8294 | 0.582    |
| later | tfidf-rf     | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.7946 | 0.878   | 0.8312  | 0.8529   | 0.8102 | 0.5604   |
| later | tfidf-ridge  | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.7653 | 0.8589  | 0.7952  | 0.8139   | 0.7779 | 0.5522   |
| later | tfidf-sgd    | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8115 | 0.9079  | 0.8489  | 0.8646   | 0.8305 | 0.5669   |
| later | tfidf-svm    | class_weight | english,sinhala,singlish,tamil,tamilish | unstamped | 0.8307 | —       | —       | —        | —      | —        |
| later | tfidf-svm    | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8308 | 0.918   | 0.8666  | 0.8793   | 0.8528 | 0.6127   |

## Intent baselines — mono-fit dev

| era   | model        | arm  | train    | fit   | language | score  |
|:------|:-------------|:-----|:---------|:------|:---------|:-------|
| later | majority     | none | english  | train | english  | 0.0005 |
| later | tfidf-cnb    | none | english  | train | english  | 0.7701 |
| later | tfidf-knn    | none | english  | train | english  | 0.8359 |
| later | tfidf-logreg | none | english  | train | english  | 0.8901 |
| later | tfidf-mnb    | none | english  | train | english  | 0.8904 |
| later | tfidf-rf     | none | english  | train | english  | 0.86   |
| later | tfidf-ridge  | none | english  | train | english  | 0.8565 |
| later | tfidf-sgd    | none | english  | train | english  | 0.8967 |
| later | tfidf-svm    | none | english  | train | english  | 0.9031 |
| later | majority     | none | sinhala  | train | sinhala  | 0.0005 |
| later | tfidf-cnb    | none | sinhala  | train | sinhala  | 0.8158 |
| later | tfidf-knn    | none | sinhala  | train | sinhala  | 0.8737 |
| later | tfidf-logreg | none | sinhala  | train | sinhala  | 0.919  |
| later | tfidf-mnb    | none | sinhala  | train | sinhala  | 0.9166 |
| later | tfidf-rf     | none | sinhala  | train | sinhala  | 0.8805 |
| later | tfidf-ridge  | none | sinhala  | train | sinhala  | 0.891  |
| later | tfidf-sgd    | none | sinhala  | train | sinhala  | 0.9159 |
| later | tfidf-svm    | none | sinhala  | train | sinhala  | 0.9251 |
| later | majority     | none | singlish | train | singlish | 0.0005 |
| later | tfidf-cnb    | none | singlish | train | singlish | 0.8221 |
| later | tfidf-knn    | none | singlish | train | singlish | 0.8708 |
| later | tfidf-logreg | none | singlish | train | singlish | 0.918  |
| later | tfidf-mnb    | none | singlish | train | singlish | 0.9116 |
| later | tfidf-rf     | none | singlish | train | singlish | 0.8832 |
| later | tfidf-ridge  | none | singlish | train | singlish | 0.885  |
| later | tfidf-sgd    | none | singlish | train | singlish | 0.9151 |
| later | tfidf-svm    | none | singlish | train | singlish | 0.9261 |
| later | majority     | none | tamil    | train | tamil    | 0.0005 |
| later | tfidf-cnb    | none | tamil    | train | tamil    | 0.8274 |
| later | tfidf-knn    | none | tamil    | train | tamil    | 0.8464 |
| later | tfidf-logreg | none | tamil    | train | tamil    | 0.9095 |
| later | tfidf-mnb    | none | tamil    | train | tamil    | 0.9007 |
| later | tfidf-rf     | none | tamil    | train | tamil    | 0.8823 |
| later | tfidf-ridge  | none | tamil    | train | tamil    | 0.8845 |
| later | tfidf-sgd    | none | tamil    | train | tamil    | 0.9044 |
| later | tfidf-svm    | none | tamil    | train | tamil    | 0.9156 |
| later | majority     | none | tamilish | train | tamilish | 0.0005 |
| later | tfidf-cnb    | none | tamilish | train | tamilish | 0.8357 |
| later | tfidf-knn    | none | tamilish | train | tamilish | 0.8763 |
| later | tfidf-logreg | none | tamilish | train | tamilish | 0.9127 |
| later | tfidf-mnb    | none | tamilish | train | tamilish | 0.9292 |
| later | tfidf-rf     | none | tamilish | train | tamilish | 0.8779 |
| later | tfidf-ridge  | none | tamilish | train | tamilish | 0.899  |
| later | tfidf-sgd    | none | tamilish | train | tamilish | 0.9187 |
| later | tfidf-svm    | none | tamilish | train | tamilish | 0.9233 |

## Intent baselines — mono-fit test

| era   | model        | arm  | train    | fit       | language | score  |
|:------|:-------------|:-----|:---------|:----------|:---------|:-------|
| later | majority     | none | english  | train+dev | english  | 0.0003 |
| later | tfidf-cnb    | none | english  | train+dev | english  | 0.7915 |
| later | tfidf-knn    | none | english  | train+dev | english  | 0.8498 |
| later | tfidf-logreg | none | english  | train+dev | english  | 0.9032 |
| later | tfidf-mnb    | none | english  | train+dev | english  | 0.8852 |
| later | tfidf-rf     | none | english  | train+dev | english  | 0.8742 |
| later | tfidf-ridge  | none | english  | train+dev | english  | 0.8602 |
| later | tfidf-sgd    | none | english  | train+dev | english  | 0.9039 |
| later | tfidf-svm    | none | english  | train+dev | english  | 0.9105 |
| later | majority     | none | sinhala  | train+dev | sinhala  | 0.0003 |
| later | tfidf-cnb    | none | sinhala  | train+dev | sinhala  | 0.6661 |
| later | tfidf-knn    | none | sinhala  | train+dev | sinhala  | 0.7955 |
| later | tfidf-logreg | none | sinhala  | train+dev | sinhala  | 0.8234 |
| later | tfidf-mnb    | none | sinhala  | train+dev | sinhala  | 0.8269 |
| later | tfidf-rf     | none | sinhala  | train+dev | sinhala  | 0.7914 |
| later | tfidf-ridge  | none | sinhala  | train+dev | sinhala  | 0.7651 |
| later | tfidf-sgd    | none | sinhala  | train+dev | sinhala  | 0.8144 |
| later | tfidf-svm    | none | sinhala  | train+dev | sinhala  | 0.8266 |
| later | majority     | none | singlish | train+dev | singlish | 0.0003 |
| later | tfidf-cnb    | none | singlish | train+dev | singlish | 0.7043 |
| later | tfidf-knn    | none | singlish | train+dev | singlish | 0.8135 |
| later | tfidf-logreg | none | singlish | train+dev | singlish | 0.8592 |
| later | tfidf-mnb    | none | singlish | train+dev | singlish | 0.8504 |
| later | tfidf-rf     | none | singlish | train+dev | singlish | 0.8416 |
| later | tfidf-ridge  | none | singlish | train+dev | singlish | 0.7949 |
| later | tfidf-sgd    | none | singlish | train+dev | singlish | 0.8558 |
| later | tfidf-svm    | none | singlish | train+dev | singlish | 0.8637 |
| later | majority     | none | tamil    | train+dev | tamil    | 0.0003 |
| later | tfidf-cnb    | none | tamil    | train+dev | tamil    | 0.7423 |
| later | tfidf-knn    | none | tamil    | train+dev | tamil    | 0.7558 |
| later | tfidf-logreg | none | tamil    | train+dev | tamil    | 0.8355 |
| later | tfidf-mnb    | none | tamil    | train+dev | tamil    | 0.8328 |
| later | tfidf-rf     | none | tamil    | train+dev | tamil    | 0.7991 |
| later | tfidf-ridge  | none | tamil    | train+dev | tamil    | 0.7958 |
| later | tfidf-sgd    | none | tamil    | train+dev | tamil    | 0.8387 |
| later | tfidf-svm    | none | tamil    | train+dev | tamil    | 0.8536 |
| later | majority     | none | tamilish | train+dev | tamilish | 0.0003 |
| later | tfidf-cnb    | none | tamilish | train+dev | tamilish | 0.4979 |
| later | tfidf-knn    | none | tamilish | train+dev | tamilish | 0.554  |
| later | tfidf-logreg | none | tamilish | train+dev | tamilish | 0.5925 |
| later | tfidf-mnb    | none | tamilish | train+dev | tamilish | 0.5812 |
| later | tfidf-rf     | none | tamilish | train+dev | tamilish | 0.5648 |
| later | tfidf-ridge  | none | tamilish | train+dev | tamilish | 0.5586 |
| later | tfidf-sgd    | none | tamilish | train+dev | tamilish | 0.5681 |
| later | tfidf-svm    | none | tamilish | train+dev | tamilish | 0.6079 |

## Intent baselines — transfer-fit dev

| era   | model        | arm  | train   | fit   | language | score  |
|:------|:-------------|:-----|:--------|:------|:---------|:-------|
| later | majority     | none | english | train | sinhala  | 0.0005 |
| later | tfidf-cnb    | none | english | train | sinhala  | 0.537  |
| later | tfidf-knn    | none | english | train | sinhala  | 0.581  |
| later | tfidf-logreg | none | english | train | sinhala  | 0.6304 |
| later | tfidf-mnb    | none | english | train | sinhala  | 0.6329 |
| later | tfidf-rf     | none | english | train | sinhala  | 0.5447 |
| later | tfidf-ridge  | none | english | train | sinhala  | 0.5789 |
| later | tfidf-sgd    | none | english | train | sinhala  | 0.6076 |
| later | tfidf-svm    | none | english | train | sinhala  | 0.6262 |
| later | majority     | none | english | train | singlish | 0.0005 |
| later | tfidf-cnb    | none | english | train | singlish | 0.5448 |
| later | tfidf-knn    | none | english | train | singlish | 0.6077 |
| later | tfidf-logreg | none | english | train | singlish | 0.6914 |
| later | tfidf-mnb    | none | english | train | singlish | 0.7149 |
| later | tfidf-rf     | none | english | train | singlish | 0.6448 |
| later | tfidf-ridge  | none | english | train | singlish | 0.5769 |
| later | tfidf-sgd    | none | english | train | singlish | 0.6536 |
| later | tfidf-svm    | none | english | train | singlish | 0.6618 |
| later | majority     | none | english | train | tamil    | 0.0005 |
| later | tfidf-cnb    | none | english | train | tamil    | 0.0164 |
| later | tfidf-knn    | none | english | train | tamil    | 0.0138 |
| later | tfidf-logreg | none | english | train | tamil    | 0.0132 |
| later | tfidf-mnb    | none | english | train | tamil    | 0.0166 |
| later | tfidf-rf     | none | english | train | tamil    | 0.0127 |
| later | tfidf-ridge  | none | english | train | tamil    | 0.0178 |
| later | tfidf-sgd    | none | english | train | tamil    | 0.0127 |
| later | tfidf-svm    | none | english | train | tamil    | 0.0127 |
| later | majority     | none | english | train | tamilish | 0.0005 |
| later | tfidf-cnb    | none | english | train | tamilish | 0.5094 |
| later | tfidf-knn    | none | english | train | tamilish | 0.5801 |
| later | tfidf-logreg | none | english | train | tamilish | 0.6508 |
| later | tfidf-mnb    | none | english | train | tamilish | 0.6503 |
| later | tfidf-rf     | none | english | train | tamilish | 0.6031 |
| later | tfidf-ridge  | none | english | train | tamilish | 0.547  |
| later | tfidf-sgd    | none | english | train | tamilish | 0.622  |
| later | tfidf-svm    | none | english | train | tamilish | 0.6323 |

## Intent baselines — transfer-fit test

| era   | model        | arm  | train   | fit       | language | score  |
|:------|:-------------|:-----|:--------|:----------|:---------|:-------|
| later | majority     | none | english | train+dev | sinhala  | 0.0003 |
| later | tfidf-cnb    | none | english | train+dev | sinhala  | 0.5204 |
| later | tfidf-knn    | none | english | train+dev | sinhala  | 0.5793 |
| later | tfidf-logreg | none | english | train+dev | sinhala  | 0.6224 |
| later | tfidf-mnb    | none | english | train+dev | sinhala  | 0.6235 |
| later | tfidf-rf     | none | english | train+dev | sinhala  | 0.5565 |
| later | tfidf-ridge  | none | english | train+dev | sinhala  | 0.5479 |
| later | tfidf-sgd    | none | english | train+dev | sinhala  | 0.5967 |
| later | tfidf-svm    | none | english | train+dev | sinhala  | 0.6127 |
| later | majority     | none | english | train+dev | singlish | 0.0003 |
| later | tfidf-cnb    | none | english | train+dev | singlish | 0.534  |
| later | tfidf-knn    | none | english | train+dev | singlish | 0.6181 |
| later | tfidf-logreg | none | english | train+dev | singlish | 0.6907 |
| later | tfidf-mnb    | none | english | train+dev | singlish | 0.6915 |
| later | tfidf-rf     | none | english | train+dev | singlish | 0.6653 |
| later | tfidf-ridge  | none | english | train+dev | singlish | 0.575  |
| later | tfidf-sgd    | none | english | train+dev | singlish | 0.6412 |
| later | tfidf-svm    | none | english | train+dev | singlish | 0.6675 |
| later | majority     | none | english | train+dev | tamil    | 0.0003 |
| later | tfidf-cnb    | none | english | train+dev | tamil    | 0.0207 |
| later | tfidf-knn    | none | english | train+dev | tamil    | 0.0193 |
| later | tfidf-logreg | none | english | train+dev | tamil    | 0.0151 |
| later | tfidf-mnb    | none | english | train+dev | tamil    | 0.0222 |
| later | tfidf-rf     | none | english | train+dev | tamil    | 0.014  |
| later | tfidf-ridge  | none | english | train+dev | tamil    | 0.0205 |
| later | tfidf-sgd    | none | english | train+dev | tamil    | 0.0142 |
| later | tfidf-svm    | none | english | train+dev | tamil    | 0.0142 |
| later | majority     | none | english | train+dev | tamilish | 0.0003 |
| later | tfidf-cnb    | none | english | train+dev | tamilish | 0.3305 |
| later | tfidf-knn    | none | english | train+dev | tamilish | 0.3754 |
| later | tfidf-logreg | none | english | train+dev | tamilish | 0.4204 |
| later | tfidf-mnb    | none | english | train+dev | tamilish | 0.414  |
| later | tfidf-rf     | none | english | train+dev | tamilish | 0.3964 |
| later | tfidf-ridge  | none | english | train+dev | tamilish | 0.3683 |
| later | tfidf-sgd    | none | english | train+dev | tamilish | 0.3949 |
| later | tfidf-svm    | none | english | train+dev | tamilish | 0.4167 |

## Priority baselines — pooled-fit dev

| era   | model                | arm          | train                                   | fit   |    all | english | sinhala | singlish | tamil  | tamilish |
|:------|:---------------------|:-------------|:----------------------------------------|:------|-------:|:--------|:--------|:---------|:-------|:---------|
| later | intent-chained       | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8964 | 0.8919  | 0.9025  | 0.901    | 0.8865 | 0.9002   |
| later | intent-lookup-oracle | none         | english,sinhala,singlish,tamil,tamilish | train | 0.9147 | 0.9147  | 0.9147  | 0.9147   | 0.9147 | 0.9147   |
| later | majority             | none         | english,sinhala,singlish,tamil,tamilish | train | 0.2302 | 0.2302  | 0.2302  | 0.2302   | 0.2302 | 0.2302   |
| later | tfidf-cnb            | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.8606 | 0.8572  | 0.8628  | 0.8625   | 0.8588 | 0.8618   |
| later | tfidf-cnb            | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8606 | 0.8572  | 0.8628  | 0.8625   | 0.8588 | 0.8618   |
| later | tfidf-cnb            | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8586 | 0.8553  | 0.8571  | 0.8585   | 0.8573 | 0.8651   |
| later | tfidf-knn            | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.8823 | 0.8812  | 0.8827  | 0.8861   | 0.8762 | 0.885    |
| later | tfidf-knn            | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8823 | 0.8812  | 0.8827  | 0.8861   | 0.8762 | 0.885    |
| later | tfidf-knn            | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8671 | 0.8561  | 0.868   | 0.8706   | 0.858  | 0.8829   |
| later | tfidf-logreg         | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.8947 | 0.8884  | 0.8984  | 0.8939   | 0.8909 | 0.9017   |
| later | tfidf-logreg         | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8884 | 0.886   | 0.8912  | 0.8907   | 0.8847 | 0.8894   |
| later | tfidf-logreg         | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8989 | 0.8927  | 0.9011  | 0.9037   | 0.8986 | 0.8986   |
| later | tfidf-mnb            | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.8673 | 0.8667  | 0.8675  | 0.8655   | 0.8666 | 0.8706   |
| later | tfidf-mnb            | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8673 | 0.8667  | 0.8675  | 0.8655   | 0.8666 | 0.8706   |
| later | tfidf-mnb            | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8672 | 0.8587  | 0.8666  | 0.8637   | 0.8692 | 0.8781   |
| later | tfidf-rf             | class_weight | english,sinhala,singlish,tamil,tamilish | train |  0.885 | 0.8873  | 0.8777  | 0.8913   | 0.8871 | 0.8822   |
| later | tfidf-rf             | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8707 | 0.8728  | 0.8802  | 0.8781   | 0.8633 | 0.8584   |
| later | tfidf-rf             | ros          | english,sinhala,singlish,tamil,tamilish | train |  0.886 | 0.8876  | 0.8865  | 0.8936   | 0.8825 | 0.8797   |
| later | tfidf-ridge          | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.9023 | 0.891   | 0.9067  | 0.9071   | 0.8994 | 0.9074   |
| later | tfidf-ridge          | none         | english,sinhala,singlish,tamil,tamilish | train | 0.9009 | 0.8907  | 0.9014  | 0.9043   | 0.9019 | 0.9057   |
| later | tfidf-ridge          | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8994 | 0.8907  | 0.899   | 0.9092   | 0.8933 | 0.905    |
| later | tfidf-sgd            | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.8933 | 0.8721  | 0.9085  | 0.9024   | 0.8806 | 0.9021   |
| later | tfidf-sgd            | none         | english,sinhala,singlish,tamil,tamilish | train | 0.8925 | 0.8813  | 0.9047  | 0.9028   | 0.877  | 0.8962   |
| later | tfidf-sgd            | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8951 | 0.886   | 0.9049  | 0.9035   | 0.8854 | 0.8955   |
| later | tfidf-svm            | class_weight | english,sinhala,singlish,tamil,tamilish | train | 0.9013 | 0.8939  | 0.907   | 0.9049   | 0.8995 | 0.901    |
| later | tfidf-svm            | none         | english,sinhala,singlish,tamil,tamilish | train | 0.9008 | 0.8938  | 0.9089  | 0.9064   | 0.8949 | 0.9002   |
| later | tfidf-svm            | ros          | english,sinhala,singlish,tamil,tamilish | train | 0.8998 | 0.8956  | 0.907   | 0.9019   | 0.8919 | 0.9023   |

## Priority baselines — pooled-fit test

| era   | model                | arm          | train                                   | fit       | all    | english | sinhala | singlish | tamil  | tamilish |
|:------|:---------------------|:-------------|:----------------------------------------|:----------|:-------|:--------|:--------|:---------|:-------|:---------|
| later | intent-chained       | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8557 | 0.8855  | 0.8699  | 0.8741   | 0.8648 | 0.7846   |
| later | intent-lookup-oracle | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.9051 | 0.9051  | 0.9051  | 0.9051   | 0.9051 | 0.9051   |
| later | majority             | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.2361 | 0.2361  | 0.2361  | 0.2361   | 0.2361 | 0.2361   |
| later | tfidf-cnb            | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8422 | 0.8643  | 0.8479  | 0.854    | 0.8653 | 0.7782   |
| later | tfidf-cnb            | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8422 | 0.8643  | 0.8479  | 0.854    | 0.8653 | 0.7782   |
| later | tfidf-cnb            | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8269 | 0.8613  | 0.8326  | 0.8392   | 0.8475 | 0.7533   |
| later | tfidf-knn            | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8379 | 0.8803  | 0.8541  | 0.8594   | 0.8561 | 0.7306   |
| later | tfidf-logreg         | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8689 | 0.8915  | 0.8826  | 0.8837   | 0.8857 | 0.8015   |
| later | tfidf-logreg         | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8677 | 0.8974  | 0.8768  | 0.883    | 0.8831 | 0.7925   |
| later | tfidf-logreg         | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8706 | 0.8987  | 0.881   | 0.8889   | 0.8849 | 0.7985   |
| later | tfidf-mnb            | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8452 | 0.8724  | 0.8539  | 0.863    | 0.8634 | 0.7754   |
| later | tfidf-rf             | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.858  | 0.8864  | 0.8575  | 0.879    | 0.8787 | 0.7849   |
| later | tfidf-ridge          | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8754 | 0.9002  | 0.8868  | 0.894    | 0.8958 | 0.7986   |
| later | tfidf-sgd            | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8603 | 0.891   | 0.872   | 0.8781   | 0.8775 | 0.7798   |
| later | tfidf-sgd            | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8631 | 0.8932  | 0.877   | 0.8801   | 0.881  | 0.7818   |
| later | tfidf-sgd            | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8659 | 0.8953  | 0.8802  | 0.8831   | 0.8853 | 0.7805   |
| later | tfidf-svm            | class_weight | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8734 | 0.905   | 0.8848  | 0.8918   | 0.8854 | 0.7984   |
| later | tfidf-svm            | none         | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8716 | 0.9007  | 0.8854  | 0.8873   | 0.8863 | 0.7962   |
| later | tfidf-svm            | ros          | english,sinhala,singlish,tamil,tamilish | train+dev | 0.8683 | 0.8988  | 0.8781  | 0.8886   | 0.8876 | 0.7842   |

## Priority baselines — mono-fit dev

| era     | model                | arm          | train    | fit       | language | score  |
|:--------|:---------------------|:-------------|:---------|:----------|:---------|:-------|
| initial | intent-chained       | none         | english  | unstamped | english  | 0.8931 |
| initial | intent-lookup-oracle | none         | english  | unstamped | english  | 0.9147 |
| initial | majority             | none         | english  | unstamped | english  | 0.2302 |
| initial | tfidf-cnb            | class_weight | english  | unstamped | english  | 0.8622 |
| initial | tfidf-cnb            | none         | english  | unstamped | english  | 0.8622 |
| initial | tfidf-cnb            | ros          | english  | unstamped | english  | 0.8536 |
| initial | tfidf-logreg         | class_weight | english  | unstamped | english  | 0.8997 |
| initial | tfidf-logreg         | none         | english  | unstamped | english  | 0.8827 |
| initial | tfidf-logreg         | ros          | english  | unstamped | english  | 0.8937 |
| initial | tfidf-sgd            | class_weight | english  | unstamped | english  | 0.8724 |
| initial | tfidf-sgd            | none         | english  | unstamped | english  | 0.8667 |
| initial | tfidf-sgd            | ros          | english  | unstamped | english  | 0.8647 |
| initial | tfidf-svm            | class_weight | english  | unstamped | english  | 0.8964 |
| initial | tfidf-svm            | none         | english  | unstamped | english  | 0.8999 |
| initial | tfidf-svm            | ros          | english  | unstamped | english  | 0.8946 |
| later   | tfidf-knn            | class_weight | english  | train     | english  | 0.8796 |
| later   | tfidf-knn            | none         | english  | train     | english  | 0.8796 |
| later   | tfidf-mnb            | class_weight | english  | train     | english  | 0.8599 |
| later   | tfidf-mnb            | none         | english  | train     | english  | 0.8599 |
| later   | tfidf-rf             | ros          | english  | train     | english  | 0.8836 |
| later   | tfidf-ridge          | class_weight | english  | train     | english  | 0.9003 |
| initial | intent-chained       | none         | sinhala  | unstamped | sinhala  | 0.9011 |
| initial | intent-lookup-oracle | none         | sinhala  | unstamped | sinhala  | 0.9147 |
| initial | majority             | none         | sinhala  | unstamped | sinhala  | 0.2302 |
| initial | tfidf-cnb            | class_weight | sinhala  | unstamped | sinhala  | 0.8639 |
| initial | tfidf-cnb            | none         | sinhala  | unstamped | sinhala  | 0.8639 |
| initial | tfidf-cnb            | ros          | sinhala  | unstamped | sinhala  | 0.8569 |
| initial | tfidf-logreg         | class_weight | sinhala  | unstamped | sinhala  | 0.9001 |
| initial | tfidf-logreg         | none         | sinhala  | unstamped | sinhala  | 0.8891 |
| initial | tfidf-logreg         | ros          | sinhala  | unstamped | sinhala  | 0.9062 |
| initial | tfidf-sgd            | class_weight | sinhala  | unstamped | sinhala  | 0.8836 |
| initial | tfidf-sgd            | none         | sinhala  | unstamped | sinhala  | 0.8852 |
| initial | tfidf-sgd            | ros          | sinhala  | unstamped | sinhala  | 0.8891 |
| initial | tfidf-svm            | class_weight | sinhala  | unstamped | sinhala  | 0.9079 |
| initial | tfidf-svm            | none         | sinhala  | unstamped | sinhala  | 0.907  |
| initial | tfidf-svm            | ros          | sinhala  | unstamped | sinhala  | 0.9025 |
| later   | tfidf-knn            | class_weight | sinhala  | train     | sinhala  | 0.8939 |
| later   | tfidf-knn            | none         | sinhala  | train     | sinhala  | 0.8939 |
| later   | tfidf-mnb            | class_weight | sinhala  | train     | sinhala  | 0.8717 |
| later   | tfidf-mnb            | none         | sinhala  | train     | sinhala  | 0.8717 |
| later   | tfidf-rf             | ros          | sinhala  | train     | sinhala  | 0.8926 |
| later   | tfidf-ridge          | class_weight | sinhala  | train     | sinhala  | 0.9104 |
| initial | intent-chained       | none         | singlish | unstamped | singlish | 0.904  |
| initial | intent-lookup-oracle | none         | singlish | unstamped | singlish | 0.9147 |
| initial | majority             | none         | singlish | unstamped | singlish | 0.2302 |
| initial | tfidf-cnb            | class_weight | singlish | unstamped | singlish | 0.8641 |
| initial | tfidf-cnb            | none         | singlish | unstamped | singlish | 0.8641 |
| initial | tfidf-cnb            | ros          | singlish | unstamped | singlish | 0.8667 |
| initial | tfidf-logreg         | class_weight | singlish | unstamped | singlish | 0.9017 |
| initial | tfidf-logreg         | none         | singlish | unstamped | singlish | 0.8852 |
| initial | tfidf-logreg         | ros          | singlish | unstamped | singlish | 0.9068 |
| initial | tfidf-sgd            | class_weight | singlish | unstamped | singlish | 0.886  |
| initial | tfidf-sgd            | none         | singlish | unstamped | singlish | 0.8964 |
| initial | tfidf-sgd            | ros          | singlish | unstamped | singlish | 0.8915 |
| initial | tfidf-svm            | class_weight | singlish | unstamped | singlish | 0.9115 |
| initial | tfidf-svm            | none         | singlish | unstamped | singlish | 0.9086 |
| initial | tfidf-svm            | ros          | singlish | unstamped | singlish | 0.9068 |
| later   | tfidf-knn            | class_weight | singlish | train     | singlish | 0.8925 |
| later   | tfidf-knn            | none         | singlish | train     | singlish | 0.8925 |
| later   | tfidf-mnb            | class_weight | singlish | train     | singlish | 0.8664 |
| later   | tfidf-mnb            | none         | singlish | train     | singlish | 0.8664 |
| later   | tfidf-rf             | ros          | singlish | train     | singlish | 0.8891 |
| later   | tfidf-ridge          | class_weight | singlish | train     | singlish | 0.9092 |
| initial | intent-chained       | none         | tamil    | unstamped | tamil    | 0.8921 |
| initial | intent-lookup-oracle | none         | tamil    | unstamped | tamil    | 0.9147 |
| initial | majority             | none         | tamil    | unstamped | tamil    | 0.2302 |
| initial | tfidf-cnb            | class_weight | tamil    | unstamped | tamil    | 0.8536 |
| initial | tfidf-cnb            | none         | tamil    | unstamped | tamil    | 0.8536 |
| initial | tfidf-cnb            | ros          | tamil    | unstamped | tamil    | 0.8419 |
| initial | tfidf-logreg         | class_weight | tamil    | unstamped | tamil    | 0.8966 |
| initial | tfidf-logreg         | none         | tamil    | unstamped | tamil    | 0.8821 |
| initial | tfidf-logreg         | ros          | tamil    | unstamped | tamil    | 0.8966 |
| initial | tfidf-sgd            | class_weight | tamil    | unstamped | tamil    | 0.8845 |
| initial | tfidf-sgd            | none         | tamil    | unstamped | tamil    | 0.8884 |
| initial | tfidf-sgd            | ros          | tamil    | unstamped | tamil    | 0.8774 |
| initial | tfidf-svm            | class_weight | tamil    | unstamped | tamil    | 0.9109 |
| initial | tfidf-svm            | none         | tamil    | unstamped | tamil    | 0.9017 |
| initial | tfidf-svm            | ros          | tamil    | unstamped | tamil    | 0.902  |
| later   | tfidf-knn            | class_weight | tamil    | train     | tamil    | 0.876  |
| later   | tfidf-knn            | none         | tamil    | train     | tamil    | 0.876  |
| later   | tfidf-mnb            | class_weight | tamil    | train     | tamil    | 0.8759 |
| later   | tfidf-mnb            | none         | tamil    | train     | tamil    | 0.8759 |
| later   | tfidf-rf             | ros          | tamil    | train     | tamil    | 0.8896 |
| later   | tfidf-ridge          | class_weight | tamil    | train     | tamil    | 0.8972 |
| initial | intent-chained       | none         | tamilish | unstamped | tamilish | 0.8945 |
| initial | intent-lookup-oracle | none         | tamilish | unstamped | tamilish | 0.9147 |
| initial | majority             | none         | tamilish | unstamped | tamilish | 0.2302 |
| initial | tfidf-cnb            | class_weight | tamilish | unstamped | tamilish | 0.8701 |
| initial | tfidf-cnb            | none         | tamilish | unstamped | tamilish | 0.8701 |
| initial | tfidf-cnb            | ros          | tamilish | unstamped | tamilish | 0.8739 |
| initial | tfidf-logreg         | class_weight | tamilish | unstamped | tamilish | 0.8941 |
| initial | tfidf-logreg         | none         | tamilish | unstamped | tamilish | 0.8847 |
| initial | tfidf-logreg         | ros          | tamilish | unstamped | tamilish | 0.8993 |
| initial | tfidf-sgd            | class_weight | tamilish | unstamped | tamilish | 0.8885 |
| initial | tfidf-sgd            | none         | tamilish | unstamped | tamilish | 0.8908 |
| initial | tfidf-sgd            | ros          | tamilish | unstamped | tamilish | 0.8912 |
| initial | tfidf-svm            | class_weight | tamilish | unstamped | tamilish | 0.9036 |
| initial | tfidf-svm            | none         | tamilish | unstamped | tamilish | 0.899  |
| initial | tfidf-svm            | ros          | tamilish | unstamped | tamilish | 0.9031 |
| later   | tfidf-knn            | class_weight | tamilish | train     | tamilish | 0.8927 |
| later   | tfidf-knn            | none         | tamilish | train     | tamilish | 0.8927 |
| later   | tfidf-mnb            | class_weight | tamilish | train     | tamilish | 0.8821 |
| later   | tfidf-mnb            | none         | tamilish | train     | tamilish | 0.8821 |
| later   | tfidf-rf             | ros          | tamilish | train     | tamilish | 0.888  |
| later   | tfidf-ridge          | class_weight | tamilish | train     | tamilish | 0.9005 |

## Priority baselines — mono-fit test

| era   | model                | arm          | train    | fit       | language | score  |
|:------|:---------------------|:-------------|:---------|:----------|:---------|:-------|
| later | intent-chained       | none         | english  | train+dev | english  | 0.8841 |
| later | intent-lookup-oracle | none         | english  | train+dev | english  | 0.9051 |
| later | majority             | none         | english  | train+dev | english  | 0.2361 |
| later | tfidf-cnb            | class_weight | english  | train+dev | english  | 0.8682 |
| later | tfidf-knn            | class_weight | english  | train+dev | english  | 0.8842 |
| later | tfidf-logreg         | ros          | english  | train+dev | english  | 0.8918 |
| later | tfidf-mnb            | class_weight | english  | train+dev | english  | 0.8779 |
| later | tfidf-rf             | ros          | english  | train+dev | english  | 0.8826 |
| later | tfidf-ridge          | class_weight | english  | train+dev | english  | 0.9008 |
| later | tfidf-sgd            | ros          | english  | train+dev | english  | 0.8861 |
| later | tfidf-svm            | class_weight | english  | train+dev | english  | 0.901  |
| later | intent-chained       | none         | sinhala  | train+dev | sinhala  | 0.8555 |
| later | intent-lookup-oracle | none         | sinhala  | train+dev | sinhala  | 0.9051 |
| later | majority             | none         | sinhala  | train+dev | sinhala  | 0.2361 |
| later | tfidf-cnb            | class_weight | sinhala  | train+dev | sinhala  | 0.8477 |
| later | tfidf-knn            | class_weight | sinhala  | train+dev | sinhala  | 0.8614 |
| later | tfidf-logreg         | ros          | sinhala  | train+dev | sinhala  | 0.8744 |
| later | tfidf-mnb            | class_weight | sinhala  | train+dev | sinhala  | 0.8546 |
| later | tfidf-rf             | ros          | sinhala  | train+dev | sinhala  | 0.8522 |
| later | tfidf-ridge          | class_weight | sinhala  | train+dev | sinhala  | 0.8795 |
| later | tfidf-sgd            | ros          | sinhala  | train+dev | sinhala  | 0.841  |
| later | tfidf-svm            | class_weight | sinhala  | train+dev | sinhala  | 0.876  |
| later | intent-chained       | none         | singlish | train+dev | singlish | 0.874  |
| later | intent-lookup-oracle | none         | singlish | train+dev | singlish | 0.9051 |
| later | majority             | none         | singlish | train+dev | singlish | 0.2361 |
| later | tfidf-cnb            | class_weight | singlish | train+dev | singlish | 0.8522 |
| later | tfidf-knn            | class_weight | singlish | train+dev | singlish | 0.8712 |
| later | tfidf-logreg         | ros          | singlish | train+dev | singlish | 0.8834 |
| later | tfidf-mnb            | class_weight | singlish | train+dev | singlish | 0.8665 |
| later | tfidf-rf             | ros          | singlish | train+dev | singlish | 0.8551 |
| later | tfidf-ridge          | class_weight | singlish | train+dev | singlish | 0.8911 |
| later | tfidf-sgd            | ros          | singlish | train+dev | singlish | 0.863  |
| later | tfidf-svm            | class_weight | singlish | train+dev | singlish | 0.8854 |
| later | intent-chained       | none         | tamil    | train+dev | tamil    | 0.8654 |
| later | intent-lookup-oracle | none         | tamil    | train+dev | tamil    | 0.9051 |
| later | majority             | none         | tamil    | train+dev | tamil    | 0.2361 |
| later | tfidf-cnb            | class_weight | tamil    | train+dev | tamil    | 0.8668 |
| later | tfidf-knn            | class_weight | tamil    | train+dev | tamil    | 0.8621 |
| later | tfidf-logreg         | ros          | tamil    | train+dev | tamil    | 0.8901 |
| later | tfidf-mnb            | class_weight | tamil    | train+dev | tamil    | 0.872  |
| later | tfidf-rf             | ros          | tamil    | train+dev | tamil    | 0.8825 |
| later | tfidf-ridge          | class_weight | tamil    | train+dev | tamil    | 0.8902 |
| later | tfidf-sgd            | ros          | tamil    | train+dev | tamil    | 0.8694 |
| later | tfidf-svm            | class_weight | tamil    | train+dev | tamil    | 0.8871 |
| later | intent-chained       | none         | tamilish | train+dev | tamilish | 0.7811 |
| later | intent-lookup-oracle | none         | tamilish | train+dev | tamilish | 0.9051 |
| later | majority             | none         | tamilish | train+dev | tamilish | 0.2361 |
| later | tfidf-cnb            | class_weight | tamilish | train+dev | tamilish | 0.7927 |
| later | tfidf-knn            | class_weight | tamilish | train+dev | tamilish | 0.749  |
| later | tfidf-logreg         | ros          | tamilish | train+dev | tamilish | 0.8108 |
| later | tfidf-mnb            | class_weight | tamilish | train+dev | tamilish | 0.7891 |
| later | tfidf-rf             | ros          | tamilish | train+dev | tamilish | 0.8008 |
| later | tfidf-ridge          | class_weight | tamilish | train+dev | tamilish | 0.8078 |
| later | tfidf-sgd            | ros          | tamilish | train+dev | tamilish | 0.7543 |
| later | tfidf-svm            | class_weight | tamilish | train+dev | tamilish | 0.8061 |

## Priority baselines — transfer-fit dev

| era     | model                | arm          | train   | fit       | language | score  |
|:--------|:---------------------|:-------------|:--------|:----------|:---------|:-------|
| initial | tfidf-cnb            | class_weight | english | unstamped | sinhala  | 0.6958 |
| initial | tfidf-cnb            | none         | english | unstamped | sinhala  | 0.6958 |
| initial | tfidf-cnb            | ros          | english | unstamped | sinhala  | 0.6788 |
| initial | tfidf-logreg         | class_weight | english | unstamped | sinhala  | 0.7038 |
| initial | tfidf-logreg         | none         | english | unstamped | sinhala  | 0.6741 |
| initial | tfidf-logreg         | ros          | english | unstamped | sinhala  | 0.7141 |
| initial | tfidf-sgd            | class_weight | english | unstamped | sinhala  | 0.595  |
| initial | tfidf-sgd            | none         | english | unstamped | sinhala  | 0.6043 |
| initial | tfidf-sgd            | ros          | english | unstamped | sinhala  | 0.611  |
| initial | tfidf-svm            | class_weight | english | unstamped | sinhala  | 0.696  |
| initial | tfidf-svm            | none         | english | unstamped | sinhala  | 0.6915 |
| initial | tfidf-svm            | ros          | english | unstamped | sinhala  | 0.6966 |
| later   | intent-chained       | none         | english | train     | sinhala  | 0.7066 |
| later   | intent-lookup-oracle | none         | english | train     | sinhala  | 0.9147 |
| later   | majority             | none         | english | train     | sinhala  | 0.2302 |
| later   | tfidf-knn            | class_weight | english | train     | sinhala  | 0.7235 |
| later   | tfidf-mnb            | class_weight | english | train     | sinhala  | 0.7525 |
| later   | tfidf-rf             | ros          | english | train     | sinhala  | 0.6559 |
| later   | tfidf-ridge          | class_weight | english | train     | sinhala  | 0.7007 |
| initial | tfidf-cnb            | class_weight | english | unstamped | singlish | 0.7579 |
| initial | tfidf-cnb            | none         | english | unstamped | singlish | 0.7579 |
| initial | tfidf-cnb            | ros          | english | unstamped | singlish | 0.7041 |
| initial | tfidf-logreg         | class_weight | english | unstamped | singlish | 0.7296 |
| initial | tfidf-logreg         | none         | english | unstamped | singlish | 0.6491 |
| initial | tfidf-logreg         | ros          | english | unstamped | singlish | 0.7256 |
| initial | tfidf-sgd            | class_weight | english | unstamped | singlish | 0.5387 |
| initial | tfidf-sgd            | none         | english | unstamped | singlish | 0.5441 |
| initial | tfidf-sgd            | ros          | english | unstamped | singlish | 0.5333 |
| initial | tfidf-svm            | class_weight | english | unstamped | singlish | 0.7009 |
| initial | tfidf-svm            | none         | english | unstamped | singlish | 0.6899 |
| initial | tfidf-svm            | ros          | english | unstamped | singlish | 0.709  |
| later   | intent-chained       | none         | english | train     | singlish | 0.7467 |
| later   | intent-lookup-oracle | none         | english | train     | singlish | 0.9147 |
| later   | majority             | none         | english | train     | singlish | 0.2302 |
| later   | tfidf-knn            | class_weight | english | train     | singlish | 0.7578 |
| later   | tfidf-mnb            | class_weight | english | train     | singlish | 0.7596 |
| later   | tfidf-rf             | ros          | english | train     | singlish | 0.693  |
| later   | tfidf-ridge          | class_weight | english | train     | singlish | 0.7166 |
| initial | tfidf-cnb            | class_weight | english | unstamped | tamil    | 0.1739 |
| initial | tfidf-cnb            | none         | english | unstamped | tamil    | 0.1739 |
| initial | tfidf-cnb            | ros          | english | unstamped | tamil    | 0.1743 |
| initial | tfidf-logreg         | class_weight | english | unstamped | tamil    | 0.2834 |
| initial | tfidf-logreg         | none         | english | unstamped | tamil    | 0.2749 |
| initial | tfidf-logreg         | ros          | english | unstamped | tamil    | 0.2919 |
| initial | tfidf-sgd            | class_weight | english | unstamped | tamil    | 0.2659 |
| initial | tfidf-sgd            | none         | english | unstamped | tamil    | 0.2659 |
| initial | tfidf-sgd            | ros          | english | unstamped | tamil    | 0.2659 |
| initial | tfidf-svm            | class_weight | english | unstamped | tamil    | 0.2825 |
| initial | tfidf-svm            | none         | english | unstamped | tamil    | 0.2827 |
| initial | tfidf-svm            | ros          | english | unstamped | tamil    | 0.2913 |
| later   | intent-chained       | none         | english | train     | tamil    | 0.1802 |
| later   | intent-lookup-oracle | none         | english | train     | tamil    | 0.9147 |
| later   | majority             | none         | english | train     | tamil    | 0.2302 |
| later   | tfidf-knn            | class_weight | english | train     | tamil    | 0.2613 |
| later   | tfidf-mnb            | class_weight | english | train     | tamil    | 0.2724 |
| later   | tfidf-rf             | ros          | english | train     | tamil    | 0.2341 |
| later   | tfidf-ridge          | class_weight | english | train     | tamil    | 0.2517 |
| initial | tfidf-cnb            | class_weight | english | unstamped | tamilish | 0.7174 |
| initial | tfidf-cnb            | none         | english | unstamped | tamilish | 0.7174 |
| initial | tfidf-cnb            | ros          | english | unstamped | tamilish | 0.7224 |
| initial | tfidf-logreg         | class_weight | english | unstamped | tamilish | 0.7283 |
| initial | tfidf-logreg         | none         | english | unstamped | tamilish | 0.6582 |
| initial | tfidf-logreg         | ros          | english | unstamped | tamilish | 0.7302 |
| initial | tfidf-sgd            | class_weight | english | unstamped | tamilish | 0.5147 |
| initial | tfidf-sgd            | none         | english | unstamped | tamilish | 0.5125 |
| initial | tfidf-sgd            | ros          | english | unstamped | tamilish | 0.5196 |
| initial | tfidf-svm            | class_weight | english | unstamped | tamilish | 0.6846 |
| initial | tfidf-svm            | none         | english | unstamped | tamilish | 0.674  |
| initial | tfidf-svm            | ros          | english | unstamped | tamilish | 0.6985 |
| later   | intent-chained       | none         | english | train     | tamilish | 0.7509 |
| later   | intent-lookup-oracle | none         | english | train     | tamilish | 0.9147 |
| later   | majority             | none         | english | train     | tamilish | 0.2302 |
| later   | tfidf-knn            | class_weight | english | train     | tamilish | 0.7169 |
| later   | tfidf-mnb            | class_weight | english | train     | tamilish | 0.7391 |
| later   | tfidf-rf             | ros          | english | train     | tamilish | 0.6831 |
| later   | tfidf-ridge          | class_weight | english | train     | tamilish | 0.6939 |

## Priority baselines — transfer-fit test

| era   | model                | arm          | train   | fit       | language | score  |
|:------|:---------------------|:-------------|:--------|:----------|:---------|:-------|
| later | intent-chained       | none         | english | train+dev | sinhala  | 0.6805 |
| later | intent-lookup-oracle | none         | english | train+dev | sinhala  | 0.9051 |
| later | majority             | none         | english | train+dev | sinhala  | 0.2361 |
| later | tfidf-cnb            | class_weight | english | train+dev | sinhala  | 0.6607 |
| later | tfidf-knn            | class_weight | english | train+dev | sinhala  | 0.7118 |
| later | tfidf-logreg         | ros          | english | train+dev | sinhala  | 0.7028 |
| later | tfidf-mnb            | class_weight | english | train+dev | sinhala  | 0.7385 |
| later | tfidf-rf             | ros          | english | train+dev | sinhala  | 0.6391 |
| later | tfidf-ridge          | class_weight | english | train+dev | sinhala  | 0.7061 |
| later | tfidf-sgd            | ros          | english | train+dev | sinhala  | 0.6262 |
| later | tfidf-svm            | class_weight | english | train+dev | sinhala  | 0.6925 |
| later | intent-chained       | none         | english | train+dev | singlish | 0.7252 |
| later | intent-lookup-oracle | none         | english | train+dev | singlish | 0.9051 |
| later | majority             | none         | english | train+dev | singlish | 0.2361 |
| later | tfidf-cnb            | class_weight | english | train+dev | singlish | 0.7339 |
| later | tfidf-knn            | class_weight | english | train+dev | singlish | 0.721  |
| later | tfidf-logreg         | ros          | english | train+dev | singlish | 0.6894 |
| later | tfidf-mnb            | class_weight | english | train+dev | singlish | 0.7313 |
| later | tfidf-rf             | ros          | english | train+dev | singlish | 0.6695 |
| later | tfidf-ridge          | class_weight | english | train+dev | singlish | 0.6839 |
| later | tfidf-sgd            | ros          | english | train+dev | singlish | 0.582  |
| later | tfidf-svm            | class_weight | english | train+dev | singlish | 0.667  |
| later | intent-chained       | none         | english | train+dev | tamil    | 0.1758 |
| later | intent-lookup-oracle | none         | english | train+dev | tamil    | 0.9051 |
| later | majority             | none         | english | train+dev | tamil    | 0.2361 |
| later | tfidf-cnb            | class_weight | english | train+dev | tamil    | 0.0862 |
| later | tfidf-knn            | class_weight | english | train+dev | tamil    | 0.2668 |
| later | tfidf-logreg         | ros          | english | train+dev | tamil    | 0.2553 |
| later | tfidf-mnb            | class_weight | english | train+dev | tamil    | 0.2714 |
| later | tfidf-rf             | ros          | english | train+dev | tamil    | 0.2393 |
| later | tfidf-ridge          | class_weight | english | train+dev | tamil    | 0.2571 |
| later | tfidf-sgd            | ros          | english | train+dev | tamil    | 0.2509 |
| later | tfidf-svm            | class_weight | english | train+dev | tamil    | 0.2521 |
| later | intent-chained       | none         | english | train+dev | tamilish | 0.6187 |
| later | intent-lookup-oracle | none         | english | train+dev | tamilish | 0.9051 |
| later | majority             | none         | english | train+dev | tamilish | 0.2361 |
| later | tfidf-cnb            | class_weight | english | train+dev | tamilish | 0.5895 |
| later | tfidf-knn            | class_weight | english | train+dev | tamilish | 0.5827 |
| later | tfidf-logreg         | ros          | english | train+dev | tamilish | 0.5957 |
| later | tfidf-mnb            | class_weight | english | train+dev | tamilish | 0.6119 |
| later | tfidf-rf             | ros          | english | train+dev | tamilish | 0.5216 |
| later | tfidf-ridge          | class_weight | english | train+dev | tamilish | 0.5982 |
| later | tfidf-sgd            | ros          | english | train+dev | tamilish | 0.4641 |
| later | tfidf-svm            | class_weight | english | train+dev | tamilish | 0.5707 |

## Classical model comparison — frozen test

| task      | metric      | model        | arm          | english | sinhala | singlish |  tamil | tamilish |    all |
|:----------|:------------|:-------------|:-------------|--------:|--------:|---------:|-------:|---------:|-------:|
| intent    | macro-F1    | tfidf-svm    | none         |   0.918 |  0.8666 |   0.8793 | 0.8528 |   0.6127 | 0.8308 |
| intent    | macro-F1    | tfidf-logreg | none         |  0.9096 |  0.8595 |   0.8751 | 0.8302 |   0.5854 | 0.8189 |
| intent    | macro-F1    | tfidf-sgd    | none         |  0.9079 |  0.8489 |   0.8646 | 0.8305 |   0.5669 | 0.8115 |
| intent    | macro-F1    | tfidf-mnb    | none         |  0.8853 |  0.8469 |    0.858 | 0.8294 |    0.582 | 0.8052 |
| intent    | macro-F1    | tfidf-rf     | class_weight |   0.878 |  0.8312 |   0.8529 | 0.8102 |   0.5604 | 0.7946 |
| intent    | macro-F1    | tfidf-ridge  | class_weight |  0.8589 |  0.7952 |   0.8139 | 0.7779 |   0.5522 | 0.7653 |
| intent    | macro-F1    | tfidf-knn    | none         |  0.8345 |  0.7687 |   0.7768 |  0.749 |   0.5149 | 0.7332 |
| intent    | macro-F1    | tfidf-cnb    | none         |  0.7772 |  0.6732 |   0.7194 | 0.7234 |   0.4925 | 0.6792 |
| sentiment | Negative-F1 | tfidf-svm    | class_weight |  0.7198 |  0.6412 |   0.6633 | 0.7249 |   0.5722 | 0.6653 |
| sentiment | Negative-F1 | tfidf-logreg | ros          |  0.6995 |  0.6256 |   0.6545 | 0.6776 |   0.5074 | 0.6383 |
| sentiment | Negative-F1 | tfidf-sgd    | ros          |  0.6842 |  0.5954 |   0.6218 | 0.6608 |   0.4577 | 0.6092 |
| sentiment | Negative-F1 | tfidf-mnb    | none         |  0.6059 |  0.5865 |   0.6123 | 0.6004 |   0.4878 | 0.5824 |
| sentiment | Negative-F1 | tfidf-rf     | class_weight |  0.5956 |  0.5845 |   0.5732 | 0.5871 |   0.3692 | 0.5492 |
| sentiment | Negative-F1 | tfidf-ridge  | none         |  0.6246 |  0.4855 |   0.5436 | 0.6067 |   0.3871 | 0.5354 |
| sentiment | Negative-F1 | tfidf-cnb    | ros          |  0.5139 |  0.5083 |   0.5302 | 0.5239 |   0.3738 | 0.4968 |
| sentiment | Negative-F1 | tfidf-knn    | ros          |  0.5196 |  0.4824 |   0.4932 | 0.5135 |   0.3755 | 0.4808 |
| priority  | macro-F1    | tfidf-ridge  | class_weight |  0.9002 |  0.8868 |    0.894 | 0.8958 |   0.7986 | 0.8754 |
| priority  | macro-F1    | tfidf-svm    | class_weight |   0.905 |  0.8848 |   0.8918 | 0.8854 |   0.7984 | 0.8734 |
| priority  | macro-F1    | tfidf-logreg | ros          |  0.8987 |   0.881 |   0.8889 | 0.8849 |   0.7985 | 0.8706 |
| priority  | macro-F1    | tfidf-sgd    | ros          |  0.8953 |  0.8802 |   0.8831 | 0.8853 |   0.7805 | 0.8659 |
| priority  | macro-F1    | tfidf-rf     | class_weight |  0.8864 |  0.8575 |    0.879 | 0.8787 |   0.7849 |  0.858 |
| priority  | macro-F1    | tfidf-mnb    | none         |  0.8724 |  0.8539 |    0.863 | 0.8634 |   0.7754 | 0.8452 |
| priority  | macro-F1    | tfidf-cnb    | class_weight |  0.8643 |  0.8479 |    0.854 | 0.8653 |   0.7782 | 0.8422 |
| priority  | macro-F1    | tfidf-knn    | none         |  0.8803 |  0.8541 |   0.8594 | 0.8561 |   0.7306 | 0.8379 |

## Sentiment balancing — frozen test

| model                            | family        | arm          | accuracy | negative_f1 | negative_precision | negative_recall | n_negative_pred | label_version |
|:---------------------------------|:--------------|:-------------|---------:|------------:|-------------------:|----------------:|----------------:|:--------------|
| gemma-3-1b                       | encoder       | class_weight |   0.9675 |      0.7126 |             0.8086 |          0.6369 |           768.0 | v8            |
| gemma-3-1b-multitask-shared3head | slm-multitask | class_weight |   0.9649 |      0.7042 |             0.7541 |          0.6605 |           854.0 | v8            |
| gemma-3-1b-multitask-sharedhead  | slm-multitask | class_weight |   0.9608 |      0.7048 |             0.6742 |          0.7385 |          1068.0 | v8            |
| labse                            | encoder       | class_weight |   0.9654 |      0.6963 |             0.7851 |          0.6256 |           777.0 | v8            |
| labse                            | encoder       | class_weight |   0.9658 |      0.7138 |             0.7601 |          0.6728 |           863.0 | v8            |
| mmbert                           | encoder       | class_weight |   0.9669 |         0.7 |             0.8207 |          0.6103 |           725.0 | v8            |
| muril-base                       | encoder       | class_weight |   0.9649 |       0.679 |             0.8076 |          0.5856 |           707.0 | v8            |
| tfidf-cnb                        | classical     | class_weight |   0.8904 |      0.4827 |             0.3443 |          0.8072 |          2286.0 | v8            |
| tfidf-cnb                        | classical     | none         |   0.8904 |      0.4827 |             0.3443 |          0.8072 |          2286.0 | v8            |
| tfidf-cnb                        | classical     | ros          |   0.9091 |      0.4968 |             0.3824 |          0.7087 |          1807.0 | v8            |
| tfidf-knn                        | classical     | ros          |   0.9078 |      0.4808 |             0.3737 |          0.6738 |          1758.0 | v8            |
| tfidf-logreg                     | classical     | class_weight |   0.9421 |      0.6286 |             0.5295 |          0.7733 |          1424.0 | v8            |
| tfidf-logreg                     | classical     | none         |   0.9521 |      0.4279 |             0.8762 |          0.2831 |           315.0 | v8            |
| tfidf-logreg                     | classical     | ros          |   0.9514 |      0.6383 |             0.6038 |          0.6769 |          1093.0 | v8            |
| tfidf-mnb                        | classical     | none         |   0.9401 |      0.5824 |             0.5215 |          0.6595 |          1233.0 | v8            |
| tfidf-rf                         | classical     | class_weight |   0.9541 |      0.5492 |             0.7276 |           0.441 |           591.0 | v8            |
| tfidf-ridge                      | classical     | none         |   0.9574 |      0.5354 |              0.865 |          0.3877 |           437.0 | v8            |
| tfidf-sgd                        | classical     | class_weight |   0.9541 |      0.6008 |             0.6683 |          0.5456 |           796.0 | v8            |
| tfidf-sgd                        | classical     | none         |   0.9572 |      0.6075 |             0.7244 |          0.5231 |           704.0 | v8            |
| tfidf-sgd                        | classical     | ros          |   0.9576 |      0.6092 |             0.7313 |          0.5221 |           696.0 | v8            |
| tfidf-svm                        | classical     | class_weight |   0.9578 |      0.6653 |             0.6691 |          0.6615 |           964.0 | v8            |
| tfidf-svm                        | classical     | none         |   0.9609 |      0.6161 |             0.8145 |          0.4954 |           593.0 | v8            |
| tfidf-svm                        | classical     | ros          |   0.9566 |      0.6047 |             0.7147 |          0.5241 |           715.0 | v8            |
| xlmr-base                        | encoder       | class_weight |   0.9654 |      0.7007 |             0.7742 |            0.64 |           806.0 | v8            |

## Lexicon correction — dev

| setup                                      | alpha | negative_f1 | precision | recall | accuracy | ci_low | ci_high |
|:-------------------------------------------|------:|------------:|----------:|-------:|---------:|-------:|--------:|
| model only (alpha=0)                       |   0.0 |      0.6173 |    0.5784 | 0.6618 |   0.9628 | 0.5402 |  0.6919 |
| model + lexicon (best non-zero alpha=0.05) |  0.05 |      0.6098 |    0.5653 | 0.6618 |   0.9615 |  0.532 |  0.6824 |

## Lexicon correction — dev by language

| language |  model | model+lexicon |   delta |
|:---------|-------:|--------------:|--------:|
| english  | 0.6259 |        0.6234 | -0.0025 |
| singlish | 0.6483 |        0.6345 | -0.0138 |
| sinhala  | 0.6207 |        0.6164 | -0.0043 |
| tamil    | 0.6207 |        0.6069 | -0.0138 |
| tamilish | 0.5714 |        0.5676 | -0.0039 |

## Label agreement — human gold

| task      | compared                           |   n | headline | ci_low | ci_high | agreement | cohen_kappa |
|:----------|:-----------------------------------|----:|---------:|-------:|--------:|----------:|------------:|
| sentiment | shipped labels vs human gold       | 500 |   0.7931 | 0.6667 |  0.8956 |     0.976 |      0.7804 |
| priority  | shipped labels vs human gold       | 500 |   0.7722 | 0.7258 |   0.815 |     0.804 |      0.6446 |
| sentiment | prompt v8 raw output vs human gold | 500 |   0.7812 | 0.6557 |  0.8842 |     0.972 |      0.7663 |

## Queue policies — test

|  rho | policy | high_mean_wait_mean | low_p95_wait_mean | sla_breach_rate_mean | rel_tardiness_mean |
|-----:|:-------|--------------------:|------------------:|---------------------:|-------------------:|
| 0.85 | fifo   |                5.78 |             21.29 |                0.002 |              0.001 |
| 0.85 | oracle |               0.988 |            36.107 |                  0.0 |                0.0 |
| 0.85 | random |               5.592 |             27.04 |                0.006 |              0.007 |
| 0.85 | tier   |               1.527 |            34.235 |                  0.0 |                0.0 |
| 0.85 | tus    |               1.125 |            46.805 |                  0.0 |                0.0 |
| 0.95 | fifo   |              16.757 |            42.415 |                0.018 |              0.012 |
| 0.95 | oracle |               1.299 |            74.009 |                  0.0 |                0.0 |
| 0.95 | random |              16.495 |            88.068 |                0.023 |              0.051 |
| 0.95 | tier   |               3.039 |            70.265 |                0.004 |              0.003 |
| 0.95 | tus    |               1.535 |           124.087 |                0.001 |                0.0 |
| 1.05 | fifo   |              52.456 |           100.395 |                 0.09 |                0.1 |
| 1.05 | oracle |               1.468 |           172.183 |                  0.0 |                0.0 |
| 1.05 | random |              52.038 |           334.432 |                0.068 |              0.248 |
| 1.05 | tier   |               7.186 |           164.943 |                 0.02 |              0.021 |
| 1.05 | tus    |               1.976 |           344.019 |                0.016 |              0.005 |

## Translation systems — automatic scores

| model            | Sinhala_labse_cosine | Sinhala_script_fidelity | Tamil_labse_cosine | Tamil_script_fidelity |
|:-----------------|---------------------:|------------------------:|-------------------:|----------------------:|
| Gemini 3.6 Flash |               0.8799 |                   0.749 |             0.7754 |                0.9712 |
| GPT-4.1          |               0.8806 |                  0.6454 |             0.8623 |                0.6446 |
| GPT-OSS-20B      |               0.8347 |                  0.6654 |             0.8558 |                0.7077 |

## Calibration — test by language

| task      | model        | language |     n | accuracy |    ece | macro_f1 |
|:----------|:-------------|:---------|------:|---------:|-------:|---------:|
| priority  | labse        | all      | 15395 |   0.9008 | 0.0658 |   0.8901 |
| priority  | labse        | english  |  3079 |   0.9263 | 0.0513 |   0.9229 |
| priority  | labse        | singlish |  3079 |   0.8974 | 0.0664 |   0.8817 |
| priority  | labse        | sinhala  |  3079 |   0.9224 | 0.0526 |   0.9179 |
| priority  | labse        | tamil    |  3079 |   0.9165 | 0.0577 |    0.913 |
| priority  | labse        | tamilish |  3079 |   0.8415 | 0.1071 |   0.8142 |
| priority  | tfidf-logreg | all      | 15395 |   0.8876 |  0.018 |   0.8706 |
| priority  | tfidf-logreg | english  |  3079 |   0.9078 | 0.0145 |   0.8987 |
| priority  | tfidf-logreg | singlish |  3079 |   0.9022 | 0.0159 |   0.8889 |
| priority  | tfidf-logreg | sinhala  |  3079 |   0.8967 |  0.017 |    0.881 |
| priority  | tfidf-logreg | tamil    |  3079 |   0.8944 | 0.0263 |   0.8849 |
| priority  | tfidf-logreg | tamilish |  3079 |    0.837 | 0.0235 |   0.7985 |
| sentiment | labse        | all      | 15395 |   0.9658 | 0.0265 |   0.8478 |
| sentiment | labse        | english  |  3079 |    0.976 | 0.0187 |   0.8952 |
| sentiment | labse        | singlish |  3079 |   0.9614 | 0.0317 |   0.8276 |
| sentiment | labse        | sinhala  |  3079 |   0.9662 | 0.0276 |   0.8527 |
| sentiment | labse        | tamil    |  3079 |   0.9708 |  0.023 |   0.8725 |
| sentiment | labse        | tamilish |  3079 |   0.9549 |  0.033 |   0.7854 |
| sentiment | tfidf-logreg | all      | 15395 |   0.9514 | 0.0273 |   0.8061 |
| sentiment | tfidf-logreg | english  |  3079 |   0.9584 | 0.0301 |   0.8386 |
| sentiment | tfidf-logreg | singlish |  3079 |    0.951 | 0.0262 |    0.814 |
| sentiment | tfidf-logreg | sinhala  |  3079 |   0.9467 | 0.0219 |   0.7984 |
| sentiment | tfidf-logreg | tamil    |  3079 |   0.9552 | 0.0332 |   0.8267 |
| sentiment | tfidf-logreg | tamilish |  3079 |   0.9458 | 0.0265 |   0.7393 |

## Research methods without a Swift score

| research method                   | intent | sentiment | priority |
|:----------------------------------|:-------|:----------|:---------|
| Reverse transliteration           | —      | —         | —        |
| Code-switch augmentation          | —      | —         | —        |
| Unfrozen-backbone adapters        | —      | —         | —        |
| External banking polarity lexicon | —      | —         | —        |
| SSwap augmentation                | —      | —         | —        |
| LSTM/BiLSTM/Capsule               | —      | —         | —        |
| XLM-R large                       | —      | —         | —        |
| SinLlama fine-tune                | —      | —         | —        |

## Neural score coverage — pooled and mono

| task      | labels      | family            | model                            | pooled dev | mono dev | pooled test | mono test |
|:----------|:------------|:------------------|:---------------------------------|:-----------|:---------|:------------|:----------|
| intent    | same-labels | decoder           | gemma-3-1b                       | 1/0        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | decoder           | gemma-3-270m                     | 1/0        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | 1/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | 1/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | encoder           | indicbert                        | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | encoder           | labse                            | 1/5        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | encoder           | mmbert                           | 1/5        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | encoder           | muril-base                       | 1/5        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | encoder           | twhin-bert                       | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | encoder           | xlmr-base                        | 1/5        | 0/5      | 1/5         | 0/5       |
| intent    | same-labels | probe             | canine-c-probe-cls               | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | canine-c-probe-mean              | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | gemma-3-1b-probe-last            | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | gemma-3-1b-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | gemma-3-270m-probe-last          | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | gemma-3-270m-probe-mean          | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | labse-ft-priority-probe-cls      | 0/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | labse-ft-priority-probe-mean     | 0/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | labse-ft-sentiment-probe-cls     | 0/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | labse-ft-sentiment-probe-mean    | 0/0        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | labse-probe-cls                  | 1/5        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | labse-probe-mean                 | 1/5        | 0/5      | 1/0         | 0/5       |
| intent    | same-labels | probe             | mmbert-probe-cls                 | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | mmbert-probe-mean                | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | sinbert-large-probe-cls          | 0/0        | 1/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | sinbert-large-probe-mean         | 0/0        | 1/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | sinhalaberto-probe-cls           | 0/0        | 1/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | sinhalaberto-probe-mean          | 0/0        | 1/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | twhin-bert-probe-cls             | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | twhin-bert-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | xlmr-base-probe-cls              | 1/5        | 0/5      | 0/0         | 0/5       |
| intent    | same-labels | probe             | xlmr-base-probe-mean             | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | decoder           | gemma-3-1b                       | 1/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | decoder           | gemma-3-270m                     | 1/0        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-shared3head | 1/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | decoder-multitask | gemma-3-1b-multitask-sharedhead  | 1/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | encoder           | canine-c                         | 1/0        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | encoder           | indicbert                        | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | encoder           | labse                            | 1/5        | 0/5      | 1/5         | 0/5       |
| priority  | same-labels | encoder           | mmbert                           | 1/5        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | encoder           | muril-base                       | 1/5        | 0/5      | 1/5         | 0/5       |
| priority  | same-labels | encoder           | twhin-bert                       | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | encoder           | xlmr-base                        | 1/5        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | canine-c-probe-cls               | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | canine-c-probe-mean              | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | gemma-3-1b-probe-last            | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | gemma-3-1b-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | gemma-3-270m-probe-last          | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | gemma-3-270m-probe-mean          | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | labse-ft-priority-probe-cls      | 0/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | labse-ft-priority-probe-mean     | 0/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | labse-ft-sentiment-probe-cls     | 0/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | labse-ft-sentiment-probe-mean    | 0/0        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | labse-probe-cls                  | 1/5        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | labse-probe-mean                 | 1/5        | 0/5      | 1/0         | 0/5       |
| priority  | same-labels | probe             | mmbert-probe-cls                 | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | mmbert-probe-mean                | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | sinbert-large-probe-cls          | 0/0        | 1/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | sinbert-large-probe-mean         | 0/0        | 1/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | sinhalaberto-probe-cls           | 0/0        | 1/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | sinhalaberto-probe-mean          | 0/0        | 1/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | twhin-bert-probe-cls             | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | twhin-bert-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | xlmr-base-probe-cls              | 1/5        | 0/5      | 0/0         | 0/5       |
| priority  | same-labels | probe             | xlmr-base-probe-mean             | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | decoder           | gemma-3-270m                     | 1/0        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | encoder           | canine-c                         | 1/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | encoder           | labse                            | 0/0        | 5/5      | 0/0         | 0/5       |
| sentiment | v5          | encoder           | labse-lora                       | 0/5        | 5/5      | 0/0         | 0/5       |
| sentiment | v5          | encoder           | twhin-bert                       | 0/0        | 5/5      | 0/0         | 0/5       |
| sentiment | v5          | encoder           | xlmr-base                        | 0/0        | 5/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | canine-c-probe-cls               | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | canine-c-probe-mean              | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | gemma-3-1b-probe-last            | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | gemma-3-1b-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | gemma-3-270m-probe-last          | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | gemma-3-270m-probe-mean          | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | labse-ft-priority-probe-cls      | 0/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | labse-ft-priority-probe-mean     | 0/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | labse-ft-sentiment-probe-cls     | 0/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | labse-ft-sentiment-probe-mean    | 0/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | labse-probe-cls                  | 1/5        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | labse-probe-mean                 | 1/5        | 0/5      | 1/0         | 0/5       |
| sentiment | v5          | probe             | mmbert-probe-cls                 | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | mmbert-probe-mean                | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | sinbert-large-probe-cls          | 0/0        | 1/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | sinbert-large-probe-mean         | 0/0        | 1/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | sinhalaberto-probe-cls           | 0/0        | 1/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | sinhalaberto-probe-mean          | 0/0        | 1/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | twhin-bert-probe-cls             | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | twhin-bert-probe-mean            | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | xlmr-base-probe-cls              | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v5          | probe             | xlmr-base-probe-mean             | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v8          | decoder           | gemma-3-1b                       | 1/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-shared3head | 1/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v8          | decoder-multitask | gemma-3-1b-multitask-sharedhead  | 1/0        | 0/5      | 1/0         | 0/5       |
| sentiment | v8          | encoder           | indicbert                        | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v8          | encoder           | labse                            | 1/5        | 0/5      | 1/5         | 0/5       |
| sentiment | v8          | encoder           | mmbert                           | 1/5        | 0/5      | 1/5         | 0/5       |
| sentiment | v8          | encoder           | muril-base                       | 1/5        | 0/5      | 1/5         | 0/5       |
| sentiment | v8          | encoder           | twhin-bert                       | 1/5        | 0/5      | 0/0         | 0/5       |
| sentiment | v8          | encoder           | xlmr-base                        | 1/5        | 0/5      | 1/5         | 0/5       |
