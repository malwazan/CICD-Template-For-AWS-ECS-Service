import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_cluster_template.ecs_cluster_template_stack import EcsClusterTemplateStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ecs_cluster_template/ecs_cluster_template_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsClusterTemplateStack(app, "ecs-cluster-template")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
