class CustomError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
    this.data = data;
  }
}

class AuthenticationError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 401, data);
  }
}

class AuthorizationError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 403, data);
  }
}

class NotFoundError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 404, data);
  }
}

class DatabaseError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 500, data);
  }
}

class ValidationError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 400, data);
  }
}

class APIError extends CustomError {
  constructor(message: string, data?: any) {
    super(message, 500, data);
  }
}

export {
  CustomError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  DatabaseError,
  ValidationError,
  APIError,
};
