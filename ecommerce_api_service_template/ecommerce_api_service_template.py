from aws_cdk import (
    Stack,
    CfnTag,
    aws_ecs,
    aws_ecr,
    aws_iam,
    aws_ec2,
    aws_ecs_patterns,
    aws_codecommit,
    aws_codebuild,
    aws_codepipeline,
    aws_codepipeline_actions
)
from constructs import Construct
from omegaconf import OmegaConf


class EcommerceApiServiceTemplateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: OmegaConf, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        # get the microservice name from env
        microservice_name = config.ecommerceapi.microservice_name

        # get the code commit parameters from env
        repository_name = microservice_name
        repository_constr_id = microservice_name + "-codecommit-id"
        branch_name = config.ecommerceapi.code_commit_branch_name
        repository_description = "Repository for " + microservice_name
        s3_bucket_for_code = config.ecommerceapi.code_commit_s3_bucket_for_code
        s3_object_key_for_code = config.ecommerceapi.code_commit_s3_object_key_for_code

        # Get ecr parameters from context
        ecr_repo_constr_id = microservice_name + "-ecrrepo-id"
        ecr_repo_name = microservice_name

        # Get code build parameters from context
        code_build_constr_id = microservice_name + "-codebuild-id"
        code_build_project_name = microservice_name

        # Get ecs fargate service parameters from context
        ecs_service_name = microservice_name
        ecs_service_role_contr_id = microservice_name + "ecsrole-id"
        ecs_service_role_name = microservice_name + "-ecs-taskexecution-role"
        ecs_fargate_constr_id = microservice_name + "-ecs-fargate-id"
        ecs_fargate_constr_id_prod = microservice_name + "-prod-ecs-fargate-id"
        
        # Get code pipeline parameters from context
        pipeline_constr_id = microservice_name + "-codepipeline-id"
        pipeline_name = microservice_name

        # Get vpc details
        vpc_id = config.ecommerceapi.vpc_id
        ecs_sg_id = config.ecommerceapi.ecs_sg_id
        ecs_name = config.ecommerceapi.ecs_name

         
        ### Create the repository and add the starter code. 
        # The starter code is available in the S3 bucket defined in cdk.json
        cfn_resource = aws_codecommit.CfnRepository(
            self,
            id=repository_constr_id,
            repository_name=repository_name,
            repository_description=repository_description,
            code=aws_codecommit.CfnRepository.CodeProperty(
                s3=aws_codecommit.CfnRepository.S3Property(
                    bucket=s3_bucket_for_code,
                    key=s3_object_key_for_code
                ),

                branch_name=branch_name
            )
        )
        # cfn_resource.add_property_override("Code.BranchName", branch_name)
        # cfn_resource.add_property_override("Code.S3.Bucket",s3_bucket_for_code)
        # cfn_resource.add_property_override("Code.S3.Key",s3_object_key_for_code)

        # get handle to code commit repository object to use in code pipeline source action
        codecommit_repo = aws_codecommit.Repository.from_repository_name(
            self, id="Repository", repository_name=repository_name
        )

        # Get handle to the ecr repository to use by code build
        ecr_repo = aws_ecr.Repository(
            self, 
            id=ecr_repo_constr_id, 
            repository_name=ecr_repo_name)

        # Create the starter ECS Fargate Service using AWS provided public nginx image. 
        # This will be updated later with the built image by the pipeline
        starter_image = aws_ecs.ContainerImage.from_registry(
            # name="public.ecr.aws/b4f2s5k2/project-demo-reinvent/nginx-web-app:latest"
            name="public.ecr.aws/nginx/nginx:perl"
        )
        execution_policy = aws_iam.ManagedPolicy.from_aws_managed_policy_name(
            managed_policy_name="service-role/AmazonECSTaskExecutionRolePolicy"
        )
        execution_role = aws_iam.Role(
            self,
            id=ecs_service_role_contr_id,
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[execution_policy],
            role_name=ecs_service_role_name
        )

        vpc_ref = aws_ec2.Vpc.from_lookup(
            self,
            id="vpc_ref",
            vpc_id=vpc_id
        )

        ecs_sg_ref = aws_ec2.SecurityGroup.from_security_group_id(
            self,
            id="ecs_sg_ref",
            security_group_id=ecs_sg_id
        )

        ecs_cluster_ref = aws_ecs.Cluster.from_cluster_attributes(
            self,
            id="ecs_cluster_ref",
            cluster_name=ecs_name,
            vpc=vpc_ref,
            security_groups=[ecs_sg_ref]
        )

        alb_fargate_service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, ecs_fargate_constr_id,
            #task_definition=alb_task_definition,
            assign_public_ip=True,
            security_groups=[ecs_sg_ref],
            cluster=ecs_cluster_ref,
            
            desired_count = 1,
            listener_port = 80, # listener port of the application load balancer
            min_healthy_percent=0,  # minimum number of tasks %, that can run in a service during a deployment
            max_healthy_percent=100, # maximum number of tasks %, that can run in a service during a deployment
            public_load_balancer=True, # determines whether the Load Balancer will be internet-facing
            service_name = ecs_service_name,
            cpu=512,
            memory_limit_mib=1024,

            task_image_options= {
                "image": starter_image,
                "container_name": "app",
                "execution_role": execution_role,
                "container_port": 80
            },
        )
        fargateservice = alb_fargate_service.service


        # Create the CodeBuild project that creates the Docker image, and pushes it to the ecr repository
        codebuild_project = aws_codebuild.PipelineProject(self, id=code_build_constr_id, 
            project_name=code_build_project_name,
            environment=aws_codebuild.BuildEnvironment(
                privileged=True # Required to run Docker
            ),
            build_spec=aws_codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "$(aws ecr get-login --region $AWS_DEFAULT_REGION --no-include-email)",
                            "docker build -t $REPOSITORY_URI:latest .",
                            "docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "docker push $REPOSITORY_URI:latest",
                            "docker push $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "export imageTag=$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "printf '[{\"name\":\"app\",\"imageUri\":\"%s\"}]' $REPOSITORY_URI:$imageTag > imagedefinitions.json"
                        ]
                    }
                },
                "env": {
                    # save the imageTag environment variable as a CodePipeline Variable
                     "exported-variables": ["imageTag"]
                },
                "artifacts": {
                    "files": "imagedefinitions.json",
                    "secondary-artifacts": {
                        "imagedefinitions": {
                            "files": "imagedefinitions.json",
                            "name": "imagedefinitions"
                        }
                    }
                }
            }),
            environment_variables={
                "REPOSITORY_URI": aws_codebuild.BuildEnvironmentVariable(
                    value=ecr_repo.repository_uri
                )
            }
        )

        # Grant push pull permissions on ecr repo to code build project needed for `docker push`
        ecr_repo.grant_pull_push(codebuild_project)

        # Define the source action for code pipeline
        source_output = aws_codepipeline.Artifact()
        source_action = aws_codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit",
            repository=codecommit_repo,
            output=source_output,
            code_build_clone_output=True
        )
        
        # Define the build action for code pipeline
        build_action = aws_codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=codebuild_project,
            input=source_output,
            outputs=[aws_codepipeline.Artifact("imagedefinitions")],
            execute_batch_build=False
        )

        # Define the deploy action for code pipeline
        deploy_action = aws_codepipeline_actions.EcsDeployAction(
            action_name="DeployECS",
            service=fargateservice,
            input=aws_codepipeline.Artifact("imagedefinitions")
        )

        # manual_approval_prod = aws_codepipeline_actions.ManualApprovalAction(
        #     action_name="Approve-Prod-Deploy",
        #     run_order=1
        # )
        #
        # deploy_action_prod = aws_codepipeline_actions.EcsDeployAction(
        #     action_name="DeployECS",
        #     service=fargateservice_prod,
        #     input=codepipeline.Artifact("imagedefinitions"),
        #     run_order=2
        # )

        # Create the pipeline
        aws_codepipeline.Pipeline(self, pipeline_constr_id, pipeline_name = pipeline_name,
            stages=[
                {
                    "stageName": "Source",
                    "actions": [source_action]
                }, 
                {
                    "stageName": "Build",
                    "actions": [build_action]
                }, 
                {
                    "stageName": "Deploy-NonProd",
                    "actions": [deploy_action]
                }, 
                # {
                #     "stageName": "Deploy-Prod",
                #     "actions": [
                #         manual_approval_prod,
                #         deploy_action_prod
                #     ]
                # }
            ]
        )








    