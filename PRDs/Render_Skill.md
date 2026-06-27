# **Skill: ddo-render**

## **Description**

Transforms structured YAML into the final document formats using the hermetic Python build orchestrator.

## **Inputs**

1. data\_file: Path to document\_data.yaml.  
2. template\_name: Name of the template to apply.  
3. format: Target output format (pdf, html, docx, md).

## **Pre-Condition Check**

Scan data\_file. If any string matches \[REQUIRES USER INPUT\], abort execution and warn the user.

## **Execution Logic**

1. Locate the correct template engine file based on template\_name and format in ddo/templates/.  
2. Invoke the build orchestrator:  
   uv run ddo/build.py \--data \<data\_file\> \--template \<template\_name\> \--format \<format\> \--output \<generated\_file\_path\>  
3. Capture stdout and stderr from the build script.

## **Post-Condition**

If compilation fails, output the exact error trace.

If successful, output the path to the newly generated document.

\[WAITING FOR USER REVIEW\]

Prompt the user to review the compiled document. Ask if they are ready to proceed to ddo-red-team or if they need to manually adjust the YAML.