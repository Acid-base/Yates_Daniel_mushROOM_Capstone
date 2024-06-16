// controllers/authController.js
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const User = require("../models/UserModel");

const registerUser = async (req, res) => {
  // ... (existing registerUser logic from userController)
};

const loginUser = async (req, res) => {
  // ... (existing loginUser logic from userController)
};

module.exports = {
  registerUser,
  loginUser,
};
