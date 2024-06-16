// customErrors.js

// Base Error Class
class CustomError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = this.constructor.name; // Set the name to the class name
    this.status = status;
    this.data = data;
  }
}

// Specific Error Classes
class AuthenticationError extends CustomError {
  constructor(message, status = 401, data = {}) {
    super(message, status, data);
  }
}

class AuthorizationError extends CustomError {
  constructor(message, status = 403, data = {}) {
    super(message, status, data);
  }
}

class NotFoundError extends CustomError {
  constructor(message, status = 404, data = {}) {
    super(message, status, data);
  }
}

class DatabaseError extends CustomError {
  constructor(message, status = 500, data = {}) {
    super(message, status, data);
  }
}

class ValidationError extends CustomError {
  constructor(message, status = 400, data = {}) {
    super(message, status, data);
  }
}

class APIError extends CustomError {
  constructor(message, status = 500, data = {}) {
    super(message, status, data);
  }
}

// Export all error classes
module.exports = {
  CustomError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  DatabaseError,
  ValidationError,
  APIError,
};
