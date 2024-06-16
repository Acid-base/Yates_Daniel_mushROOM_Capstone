"use strict";
exports.__esModule = true;
var jsonwebtoken_1 = require("jsonwebtoken");
var dotenv_1 = require("dotenv");
dotenv_1["default"].config();
var authenticateToken = function (req, res, next) {
    var authHeader = req.headers['authorization'];
    var token = authHeader && authHeader.split(' ')[1];
    if (!token) {
        return res.status(401).json({ error: 'Access denied, no token provided' });
    }
    try {
        var decoded = jsonwebtoken_1["default"].verify(token, process.env.JWT_SECRET);
        req.userId = decoded.userId;
        next();
    }
    catch (error) {
        res.status(400).json({ error: 'Invalid token' });
    }
};
exports["default"] = authenticateToken;
