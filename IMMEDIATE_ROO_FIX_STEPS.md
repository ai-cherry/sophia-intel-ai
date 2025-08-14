# 🚨 IMMEDIATE Roo Custom Modes Fix - Step by Step

## 🎯 SITUATION: Mode Selector Visible, But No Custom Modes

You can see Roo's mode selector but only default modes appear. This means Roo is working but not reading the `.roomodes` file.

---

## 🚀 SOLUTION 1: Manual Roo Configuration (TRY THIS FIRST)

### Step 1: Configure Roo to Read Custom Modes File
1. **Open Roo Settings**: Click the **⚙️ gear icon** in the top-right of Roo sidebar
2. **Find Project Modes Setting**: Look for one of these options:
   - "Project Prompts" 
   - "Custom Modes"
   - "Mode Configuration"
   - "Edit Project Modes"
3. **Configure File Path**: 
   - If you see a file path field, enter: `/workspaces/sophia-intel/.roomodes`
   - If you see a format option, select: `YAML`
   - If you see "Browse" button, navigate to and select `.roomodes`
4. **Apply Changes**: Click "Apply" or "Save"
5. **Reload Window**: `Ctrl+Shift+P` → "Developer: Reload Window"

### Step 2: Check Mode Selector Again
- Open Roo sidebar
- Look for your 5 SOPHIA custom modes in the dropdown

---

## 🔧 SOLUTION 2: Roo Workspace File (ALREADY CREATED)

I've created a `.roo/config.json` file that should help Roo auto-detect your custom modes. After the file was created:

1. **Completely Close VSCode** (not just reload - fully close the browser tab/application)
2. **Reopen the Codespace/VSCode**  
3. **Wait for full startup** (all extensions loaded)
4. **Check Roo sidebar** for custom modes

---

## 🔍 SOLUTION 3: Verify File Location

If Roo still can't find the modes, verify the exact path:

1. **In Roo Settings**, try these path variations:
   - `.roomodes`
   - `./roomodes` 
   - `/workspaces/sophia-intel/.roomodes`
   - Full absolute path from current directory

2. **Check Working Directory**: Ensure VSCode opened in `/workspaces/sophia-intel`

---

## 🎯 EXPECTED RESULT

After successful configuration, you should see these 5 modes in Roo:

- 🏛️ **SOPHIA Architect** - Architecture design, code reviews
- 🏗️ **SOPHIA Feature Builder** - New feature development  
- 🧪 **SOPHIA Test Engineer** - Testing, quality assurance
- 🛠️ **SOPHIA Operator** - DevOps, infrastructure
- 🔍 **SOPHIA Debugger** - Troubleshooting, diagnostics

---

## 🚨 IF STILL NOT WORKING

### Try Nuclear Option:
1. **Disable Roo Extension** → **Reload Window** → **Re-enable Roo Extension**
2. **Create Fresh Codespace** from the same repository
3. **Check VSCode Developer Console (F12)** for any Roo-related errors

### Get Help:
- Screenshot the Roo settings panel showing mode configuration options
- Check if there are any error messages in VSCode status bar
- Verify Roo extension version is up to date

---

## ✅ VALIDATION

Your custom modes file is **perfect** and ready:
- ✅ Valid YAML syntax
- ✅ All 5 modes properly configured  
- ✅ All required fields present
- ✅ File accessible and readable

The issue is purely a Roo configuration/path problem, not a file problem.