from aws_cdk import App
from cdk_project.cdk_project_stack import CdkProjectStack

app = App()

# Initialize the stack
CdkProjectStack(app, "CdkProjectStack")

app.synth()
