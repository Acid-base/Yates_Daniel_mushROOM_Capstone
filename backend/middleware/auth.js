const jwt = require('jsonwebtoken');

const secretKey = 'your_secret_key'; // Replace with your secret key

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (token == null) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  jwt.verify(token, secretKey, (err, decoded) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }

    req.userId = decoded.userId; // Attach user ID to the request object
    next();
  });
};

module.exports = authenticateToken;
