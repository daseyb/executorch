# Copyright (c) Meta Platforms, Inc. and affiliates.
# Copyright 2024-2025 Arm Limited and/or its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import logging
import unittest

import pytest

import torch
from executorch.backends.arm.test import common, conftest

from executorch.backends.arm.test.tester.arm_tester import ArmTester
from torchvision import models, transforms  # type: ignore[import-untyped]
from torchvision.models.mobilenetv2 import (  # type: ignore[import-untyped]
    MobileNet_V2_Weights,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestMobileNetV2(unittest.TestCase):
    """Tests MobileNetV2."""

    mv2 = models.mobilenetv2.mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT)
    mv2 = mv2.eval()
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    )

    # Used e.g. for quantization calibration and shape extraction in the tester
    model_example_inputs = (normalize(torch.randn((1, 3, 224, 224))),)

    def test_mv2_tosa_MI(self):
        (
            ArmTester(
                self.mv2,
                example_inputs=self.model_example_inputs,
                compile_spec=common.get_tosa_compile_spec("TOSA-0.80+MI"),
            )
            .export()
            .to_edge_transform_and_lower()
            .check_count({"torch.ops.higher_order.executorch_call_delegate": 1})
            .to_executorch()
            .run_method_and_compare_outputs()
        )

    def test_mv2_tosa_BI(self):
        (
            ArmTester(
                self.mv2,
                example_inputs=self.model_example_inputs,
                compile_spec=common.get_tosa_compile_spec("TOSA-0.80+BI"),
            )
            .quantize()
            .export()
            .to_edge_transform_and_lower()
            .check_count({"torch.ops.higher_order.executorch_call_delegate": 1})
            .to_executorch()
            .run_method_and_compare_outputs(rtol=0.001, atol=0.2, qtol=1)
        )

    @pytest.mark.slow
    @pytest.mark.corstone_fvp
    def test_mv2_u55_BI(self):
        tester = (
            ArmTester(
                self.mv2,
                example_inputs=self.model_example_inputs,
                compile_spec=common.get_u55_compile_spec(),
            )
            .quantize()
            .export()
            .to_edge_transform_and_lower()
            .to_executorch()
            .serialize()
        )
        if conftest.is_option_enabled("corstone_fvp"):
            tester.run_method_and_compare_outputs(
                rtol=0.001,
                atol=0.2,
                qtol=1,
            )

    @pytest.mark.slow
    @pytest.mark.corstone_fvp
    def test_mv2_u85_BI(self):
        tester = (
            ArmTester(
                self.mv2,
                example_inputs=self.model_example_inputs,
                compile_spec=common.get_u85_compile_spec(),
            )
            .quantize()
            .export()
            .to_edge_transform_and_lower()
            .to_executorch()
            .serialize()
        )
        if conftest.is_option_enabled("corstone_fvp"):
            tester.run_method_and_compare_outputs(
                rtol=0.001,
                atol=0.2,
                qtol=1,
            )
