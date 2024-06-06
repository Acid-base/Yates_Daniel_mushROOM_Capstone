const express = require('express');
const router = express.Router();

const userController = require('../controllers/userController');

router.get('/', userController.getUsers);

// Add other routes for creating, updating, deleting users
module.exports = router;
