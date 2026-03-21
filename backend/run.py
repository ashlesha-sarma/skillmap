#!/usr/bin/env python3
"""
SkillMap — Backend startup script
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render uses PORT env var

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # IMPORTANT: disable reload in production
        log_level="info",
    )