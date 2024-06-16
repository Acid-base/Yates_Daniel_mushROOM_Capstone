// logger/logger.js
const winston = require("winston");
require("dotenv").config(); // Load environment variables

const logLevel = process.env.LOG_LEVEL || "info"; // Get log level from environment variable

const logger = winston.createLogger({
  level: logLevel, // Use the environment variable for log level
  format: winston.format.combine(
    winston.format.timestamp({ format: "YYYY-MM-DD HH:mm:ss" }), // Add timestamp
    winston.format.json(), // Format logs as JSON
  ),
  defaultMeta: { service: "mushroom-service" },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(), // Add color to console logs
        winston.format.simple(), // Simple console output
      ),
    }),
    new winston.transports.File({ filename: "logs/error.log", level: "error" }),
    new winston.transports.File({ filename: "logs/combined.log" }),
  ],
});

// Add custom logging levels
logger.addColors({
  debug: "green",
  info: "cyan",
  warn: "yellow",
  error: "red",
  fatal: "magenta",
});

// Example usage:
logger.debug("Debug message");
logger.info("Info message");
logger.warn("Warning message");
logger.error("Error message");
logger.fatal("Fatal error message");

module.exports = logger;
