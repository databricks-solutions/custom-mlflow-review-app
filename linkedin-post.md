Collecting labels from Subject Matter Experts for Agents is an important part of ensuring your Agent is high quality. Often you want to customize the UI you show for labeling - that's why I'm excited to share a new Custom MLflow Review App template for Databricks Apps!

This template allows you to:
✅ Build custom review interfaces for MLflow traces - show only what matters to your SMEs
✅ Create domain-specific labeling schemas (ratings, categories, text feedback) that match your evaluation needs  
✅ Customize trace rendering - filter spans, hide sensitive data, present information your way
✅ Leverage AI-powered analysis to identify patterns, measure inter-rater agreement, and summarize results
✅ Deploy directly to Databricks Apps with built-in authentication and permissions management
✅ Use Claude Code's `/review-app` command for automatic customization based on your experiment

Github: https://github.com/databricks-solutions/custom-mlflow-review-app
Walkthrough video: https://youtu.be/xdvodY9-VQQ

The template comes with a production-ready FastAPI backend integrated with MLflow SDK, a React frontend with beautiful shadcn components, and comprehensive CLI tools for managing schemas, sessions, and traces.

Just clone the repo, open Claude Code and type `/review-app` - Claude will analyze your MLflow experiment and automatically customize the entire review app for your specific use case.

Perfect for teams that need more control over their human evaluation workflows than the standard Databricks review app provides. The template handles all the complexity while giving you full customization power!