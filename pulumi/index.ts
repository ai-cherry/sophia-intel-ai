import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Get config and secrets
const config = new pulumi.Config();
const stack = pulumi.getStack();

// Use ESC for sensitive values (zero-trust)
// These are pulled from Pulumi ESC, not hardcoded
const githubToken = pulumi.getSecretOutput("github_token");

// Example bucket with proper naming convention
const bucket = new aws.s3.Bucket(`sophia-${stack}-data`, {
    tags: {
        Name: `sophia-${stack}-data`,
        Environment: stack,
        Project: "sophia-intel"
    },
});

// Export the name of the bucket
export const bucketName = bucket.id;
export const bucketArn = bucket.arn;
