# 🎯 NOTION SETUP FOR SOPHIA - QUICK START GUIDE

## ✅ STEP 1: CREATE SOPHIA'S WORKSPACE

1. Open Notion in your browser
2. Create a new page: "🤖 Sophia Intelligence Hub"
3. Make it a top-level page for easy access

## ✅ STEP 2: SHARE WITH YOUR INTEGRATION

1. Click "Share" button on the page
2. Click "Add people, emails, groups, or integrations"
3. Search for your integration (should see it listed)
4. Grant "Can edit" permissions
5. Click "Invite"

## ✅ STEP 3: CREATE DATABASES (Copy & Paste Ready!)

### 📄 Business Documents Database

Create a new database and add these properties:

- Name (Title)
- Category (Select: Strategy, Financial, Operations, Marketing, Sales)
- Priority (Select: High, Medium, Low)
- Last Updated (Last edited time)
- Tags (Multi-select)
- Summary (Text)
- Insights (Text)
- Source (URL)

### 📝 Meeting Notes Database

- Title (Title)
- Date (Date)
- Attendees (Multi-select)
- Type (Select: Client Meeting, Team Sync, Strategy Session, Sales Call)
- Key Decisions (Text)
- Action Items (Text)
- Follow Up (Checkbox)
- Recording Link (URL)

### 🎯 Strategic Plans Database

- Plan Name (Title)
- Quarter (Select: Q1-Q4 2025)
- Status (Select: Planning, In Progress, Completed, On Hold)
- Objectives (Text)
- Key Results (Text)
- Progress (Number - format as percentage)
- Owner (Person)

### 📊 Market Research Database

- Research Topic (Title)
- Industry (Multi-select)
- Competitors (Multi-select)
- Date (Date)
- Key Findings (Text)
- Opportunities (Text)
- Threats (Text)
- Recommendations (Text)

### 💡 Sophia Insights Database

- Insight (Title)
- Generated Date (Created time)
- Category (Select: Business Intelligence, Market Trend, Risk Alert, Opportunity)
- Impact (Select: Critical, High, Medium, Low)
- Context (Text)
- Recommendation (Text)
- Action Taken (Checkbox)

## ✅ STEP 4: GET DATABASE IDS

For each database you create:

1. Open the database
2. Copy the URL (it contains the database ID)
3. The ID is the 32-character string before the "?"
   Example: notion.so/workspace/abc123def456... ← this part

## ✅ STEP 5: UPDATE INTEGRATION CONFIG

Add to your integrations_config.py:

"notion_knowledge": {
"enabled": True,
"status": "connected",
"workspace_page_id": "YOUR_PAGE_ID",
"databases": {
"business_documents": "DATABASE_ID_1",
"meeting_notes": "DATABASE_ID_2",
"strategic_plans": "DATABASE_ID_3",
"market_research": "DATABASE_ID_4",
"sophia_insights": "DATABASE_ID_5"
},
"stats": {"databases": 5, "integration": "active"}
}

## 🚀 THAT'S IT! Sophia can now

• Store and retrieve business documents
• Track meeting notes and action items
• Manage strategic plans with progress tracking
• Analyze market research data
• Generate and store AI insights
• Search across all knowledge bases
• Create relationships between documents

## 💡 PRO TIPS

• Use Notion's views to filter by priority/status
• Create templates for consistent data entry
• Use relations to link related documents
• Set up automation rules in Notion for notifications
• Embed charts and visualizations in pages
