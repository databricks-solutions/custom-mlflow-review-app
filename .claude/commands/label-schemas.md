# Label Schemas Management

Manage labeling schemas for your MLflow Review App. This command helps you view, create, modify, and delete schemas interactively.

## Usage

```bash
/label-schemas [action]
```

## Actions

### List Schemas (default)
```bash
/label-schemas
```
Shows all current labeling schemas in a beautiful format with details about each schema type, options, and instructions.

**Context-Aware Suggestions**: When available, references experiment summaries from `experiments/[experiment_id]_summary.md` to suggest schemas tailored to your specific agent's capabilities and use cases.

### Add New Schema
```bash
/label-schemas add [description]
```

Examples:
- `/label-schemas add quality rating from 1 to 5`
- `/label-schemas add helpfulness categorical with options: Very Helpful, Helpful, Not Helpful`
- `/label-schemas add feedback text field for comments`

**Smart Suggestions**: Leverages experiment analysis to recommend schemas appropriate for your agent type:
- **Multi-tool agents**: Tool Selection Accuracy, Multi-Step Reasoning, Resource Efficiency
- **Simple agents**: Response Quality, Task Completion, Style Consistency
- **Analytics agents**: Data Analysis Quality, Recommendation Usefulness, Error Handling

### Modify Schema
```bash
/label-schemas modify [schema_name] [changes]
```

Examples:
- `/label-schemas modify quality change range to 1-10`
- `/label-schemas modify helpfulness add option "Extremely Helpful"`
- `/label-schemas modify feedback change title to "Additional Comments"`

### Delete Schema
```bash
/label-schemas delete [schema_name]
```

Examples:
- `/label-schemas delete quality`
- `/label-schemas delete feedback`

## Implementation

This command orchestrates the following tools:
- `tools/get_review_app.py` - Get current schemas
- `tools/create_labeling_schemas.py` - Create new schemas
- `tools/update_labeling_schemas.py` - Modify existing schemas (to be created)
- `tools/delete_labeling_schemas.py` - Delete schemas (to be created)

All tools use shared utilities in `server/utils/review_apps_utils.py` for consistent API access.

## Workflow

1. **List**: Display current schemas with beautiful CLI formatting
2. **Add**: Parse natural language, show preview, ask for confirmation, then create
3. **Modify**: Parse changes, show what will change, ask for confirmation, then update
4. **Delete**: Show what will be deleted, ask for confirmation, then remove

## Confirmations

All destructive actions (modify/delete) require explicit user confirmation:
- Show exactly what will change
- Ask user to type specific confirmation phrase
- Only proceed after confirmation received