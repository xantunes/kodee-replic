# Getting Started with Kodee

## Overview

Kodee is your AI administrative assistant for managing infrastructure tasks. This guide covers the basics of interacting with Kodee and the types of tasks it can help you with.

## Supported Tasks

### DNS Management
Kodee can help you manage DNS records for your domains:
- **Create records**: Add A, AAAA, CNAME, MX, TXT, and NS records
- **List records**: View all existing records for a zone
- **Delete records**: Remove records that are no longer needed

Example: "Create an A record for www.example.com pointing to 192.168.1.1"

### Backup Management
Kodee assists with backup and recovery operations:
- **Create backups**: Initiate full or incremental backups
- **Restore backups**: Recover from a previous backup point
- **List backups**: View available backup snapshots

Example: "Create a backup of my database before the upgrade"

### Server Monitoring
Kodee can check the health and status of your infrastructure:
- **Health checks**: Verify server availability and resource usage
- **Website status**: Check if a website is up and responding

Example: "Check the health of server-01 and alert me if CPU is above 80%"

## Safety Features

Kodee includes several safety mechanisms:
- **Destructive action confirmation**: Operations like deleting DNS records or restoring backups require your explicit confirmation
- **Input sanitization**: All user inputs are validated to prevent injection attacks
- **Rate limiting**: API endpoints are protected against abuse

## Tips for Best Results

1. Be specific about domain names, server IDs, and record types
2. Confirm destructive operations when prompted
3. Use session IDs to maintain conversation context across multiple messages
