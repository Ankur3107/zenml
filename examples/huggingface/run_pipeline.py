#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

import click
import sequence_classification
import token_classification
from sequence_classification import SequenceClassificationConfig
from token_classification import TokenClassificationConfig


@click.command()
@click.option(
    "--nlp_task",
    default="token-classification",
    help="Name NLP task i.e. token-classificaion",
)
@click.option(
    "--pretrained_model",
    default="distilbert-base-uncased",
    help="Pretrained model name from huggingface hub",
)
@click.option(
    "--batch_size",
    default=8,
    help="Batch Size for training",
)
@click.option(
    "--epochs",
    default=3,
    help="Number of epochs for training",
)
def main(nlp_task: str, pretrained_model: str, batch_size: int, epochs: int):
    if nlp_task == "token-classification":
        # Run Pipeline
        token_classification_config = TokenClassificationConfig(
            pretrained_model=pretrained_model,
            epochs=epochs,
            batch_size=batch_size,
        )
        pipeline = token_classification.token_classifier_train_eval_pipeline(
            importer=token_classification.data_importer(
                token_classification_config
            ),
            load_tokenizer=token_classification.load_tokenizer(
                token_classification_config
            ),
            tokenization=token_classification.tokenization(
                token_classification_config
            ),
            trainer=token_classification.trainer(token_classification_config),
            evaluator=token_classification.evaluator(
                token_classification_config
            ),
        )
        pipeline.run()

    elif nlp_task == "sequence-classification":
        # Run Pipeline
        sequence_classification_config = SequenceClassificationConfig(
            pretrained_model=pretrained_model,
            epochs=epochs,
            batch_size=batch_size,
        )
        pipeline = sequence_classification.seq_classifier_train_eval_pipeline(
            importer=sequence_classification.data_importer(
                sequence_classification_config
            ),
            load_tokenizer=sequence_classification.load_tokenizer(
                sequence_classification_config
            ),
            tokenization=sequence_classification.tokenization(
                sequence_classification_config
            ),
            trainer=sequence_classification.trainer(
                sequence_classification_config
            ),
            evaluator=sequence_classification.evaluator(
                sequence_classification_config
            ),
        )
        pipeline.run()


if __name__ == "__main__":
    main()