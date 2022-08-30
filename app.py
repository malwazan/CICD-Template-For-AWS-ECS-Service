#!/usr/bin/env python3
import os
import aws_cdk as cdk
from omegaconf import OmegaConf

# local imports
from ecs_cluster_template.ecs_cluster_template_stack import EcsClusterTemplateStack
from ecommerce_api_service_template.ecommerce_api_service_template import EcommerceApiServiceTemplateStack

# load environment yaml
deploy_env = "dev"
conf = OmegaConf.load("environments/{0}.yaml".format(deploy_env))


app = cdk.App()
EcsClusterTemplateStack(app, "EcsClusterTemplateStack",
    env=cdk.Environment(account=conf.aws.account, region=conf.aws.region),
)

EcommerceApiServiceTemplateStack(app, "EcommerceApiServiceTemplateStack",
    config=conf,
    env=cdk.Environment(account=conf.aws.account, region=conf.aws.region),
)


app.synth()
