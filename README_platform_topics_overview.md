# Platform Topics Overview Analyzer

A comprehensive script that analyzes and extracts the top 5 topics/themes from both Linear and Asana platforms using advanced text analysis techniques.

## Features

🔧 **Linear Integration**

- Extracts content from teams, issues, labels, and projects
- Analyzes issue titles, descriptions, and labels
- Supports GraphQL API queries with proper authentication

🎯 **Asana Integration**

- Connects to workspaces and projects
- Analyzes project names, task titles, descriptions, and tags
- Uses REST API with Bearer token authentication

🔍 **Advanced Topic Analysis**

- Sophisticated text processing and keyword extraction
- Domain-specific categorization (Development, Product, Business, Operations, Project Management)
- Frequency analysis and relevance scoring
- Bigram and trigram phrase extraction
- Topic examples and context preservation

📊 **Comprehensive Reporting**

- Cross-platform topic comparison
- Category distribution analysis
- Detailed content statistics
- JSON exports for further analysis
- Real-time console output with progress tracking

## Prerequisites

1. **API Access**: Ensure both Linear and Asana integrations are configured in `integrations_config.py`
2. **Dependencies**: The script uses existing client implementations from the Sophia platform

## Usage

### Basic Execution

```bash
python3 get_platform_topics_overview.py
```

### What the Script Does

1. **Phase 1: Content Extraction**

   - Connects to Linear and Asana APIs
   - Extracts structured content from both platforms
   - Handles errors gracefully and continues with available data

2. **Phase 2: Topic Analysis**

   - Processes text using advanced NLP techniques
   - Categorizes content into domain-specific topics
   - Calculates relevance scores and frequencies

3. **Phase 3: Results Presentation**

   - Displays comprehensive analysis in the console
   - Shows top 5 topics from each platform
   - Provides cross-platform insights and comparisons

4. **Phase 4: Data Export**
   - Saves detailed JSON reports with timestamps
   - Exports individual platform analyses
   - Creates combined overview report

## Output Files

The script generates three JSON files with timestamps:

- `linear_topics_analysis_YYYYMMDD_HHMMSS.json` - Detailed Linear analysis
- `asana_topics_analysis_YYYYMMDD_HHMMSS.json` - Detailed Asana analysis
- `platform_topics_overview_YYYYMMDD_HHMMSS.json` - Combined overview

## Topic Categories

The analyzer recognizes these domain categories:

### Development

Keywords: frontend, backend, api, database, ui, ux, react, python, docker, testing, security, etc.

### Product

Keywords: feature, user, customer, experience, design, prototype, feedback, launch, etc.

### Business

Keywords: sales, marketing, revenue, growth, client, roi, analytics, strategy, etc.

### Operations

Keywords: process, workflow, automation, efficiency, documentation, monitoring, etc.

### Project Management

Keywords: planning, sprint, scrum, agile, backlog, milestone, timeline, etc.

## Sample Output

```
================================================================================
🚀 PLATFORM TOPICS OVERVIEW
================================================================================
Analysis Date: 2025-09-04 12:40:29

🔧 LINEAR TOPICS ANALYSIS
--------------------------------------------------
Content Analyzed: 96 items
Content Types: {'team_name': 9, 'issue_title': 23, 'issue_description': 14, 'label': 18, 'project_name': 20, 'project_description': 12}
Keywords Extracted: 334 unique

Top 5 Linear Topics:
1. General (category)
   📊 Relevance Score: 50.19%
   📈 Frequency: 88
   🔑 Key Terms: buzz, migrated, payready, com, access
   💬 Example: "Change Management"
```

## Key Insights Provided

- **Platform Focus Comparison**: Which topics each platform emphasizes
- **Content Distribution**: Types of content analyzed from each platform
- **Common Topics**: Overlapping themes across platforms
- **Category Strengths**: Which platform shows stronger focus in each domain
- **Usage Patterns**: Understanding how teams use each platform

## Error Handling

The script includes robust error handling:

- Continues analysis even if one platform fails
- Logs warnings for partial failures
- Provides meaningful error messages
- Gracefully handles API rate limits and timeouts

## Technical Implementation

### Text Processing Features

- Stop word filtering with comprehensive business vocabulary
- Minimum word length filtering (3+ characters)
- Special character normalization
- Phrase extraction (bigrams and trigrams)
- Context-aware keyword weighting

### Analysis Algorithms

- TF-IDF inspired frequency analysis
- Category-based relevance scoring
- Cross-platform topic matching
- Statistical significance testing
- Relevance threshold filtering (>5% for categories, >10% for phrases)

## Benefits for Business Intelligence

1. **Platform Optimization**: Understand how teams use different tools
2. **Content Strategy**: Identify most discussed topics and themes
3. **Resource Allocation**: See where teams focus their efforts
4. **Process Improvement**: Discover workflow patterns and bottlenecks
5. **Cross-Team Insights**: Find common themes across different teams

## Customization Options

The script can be easily modified to:

- Adjust relevance score thresholds
- Add new domain categories
- Change content limits per platform
- Modify text processing parameters
- Add additional output formats

## Performance Considerations

- Limits content extraction to prevent overwhelming analysis
- Uses async operations for efficient API calls
- Implements proper session management
- Includes timeout handling for long-running operations

## Integration with Sophia Platform

This script leverages the existing Sophia intelligence platform:

- Uses established API client patterns
- Follows platform logging conventions
- Integrates with resource management system
- Maintains consistent error handling approaches

---

**Created**: September 2025  
**Author**: Sophia AI Platform  
**Version**: 1.0.0
