import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 15, // Limit each IP to 15 requests per minute
  message: { error: 'Too many requests, please try again later.' },
});

export default apiLimiter;
