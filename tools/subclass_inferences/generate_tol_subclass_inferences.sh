#!/bin/bash

# Small script to generate the ideo subclass inferences.
# This script exists for use in onto_tool as it runs tools on a file-by-file basis.

# Initialize variables
OUTPUT_DIR=$1

# Output path must exist.
python tools/subclass_inferences/materialize_subclass_inferences.py $OUTPUT_DIR/models/ontologies/tolSubClassAssertions.ttl models/ontologies/*.ttl
