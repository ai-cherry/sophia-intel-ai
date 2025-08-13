// Pulumi ESC Integration for SOPHIA
// This file demonstrates how to access ESC secrets in your Pulumi code

import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as github from "@pulumi/github";

// Get secrets from Pulumi ESC
const githubToken = pulumi.getSecretOutput("github_token");

// Configure providers with ESC secrets
const githubProvider = new github.Provider("github-provider", {
    token: githubToken,
});

// Example GitHub resources using the ESC-configured provider
const exampleRepo = new github.Repository("sophia-example-repo", {
    name: "sophia-example",
    description: "Example repository created via Pulumi with ESC",
    visibility: "private",
}, { provider: githubProvider });

// Export resources
export const repoUrl = exampleRepo.htmlUrl;
