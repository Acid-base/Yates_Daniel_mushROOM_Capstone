"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
exports.__esModule = true;
exports.seedDatabase = exports.fetchAndStoreMushroomData = exports.disconnectFromDatabase = exports.connectToDatabase = void 0;
var mongoose_1 = require("mongoose");
var axios_1 = require("axios");
var customErrors_1 = require("../middleware/customErrors");
var MushroomModel_1 = require("../models/MushroomModel");
var BlogPostModel_1 = require("../models/BlogPostModel");
var FavoriteModel_1 = require("../models/FavoriteModel");
var UserModel_1 = require("../models/UserModel"); // This now imports the updated User model
var dotenv_1 = require("dotenv");
dotenv_1["default"].config();
var databaseUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/mydatabase';
var connection;
function connectToDatabase() {
    return __awaiter(this, void 0, void 0, function () {
        var error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    return [4 /*yield*/, mongoose_1["default"].connect(databaseUri, {
                            useNewUrlParser: true,
                            useUnifiedTopology: true
                        })];
                case 1:
                    connection = _a.sent();
                    console.log('Connected to MongoDB');
                    return [2 /*return*/, connection];
                case 2:
                    error_1 = _a.sent();
                    throw new customErrors_1.DatabaseError("MongoDB connection error: ".concat(error_1.message));
                case 3: return [2 /*return*/];
            }
        });
    });
}
exports.connectToDatabase = connectToDatabase;
function disconnectFromDatabase() {
    return __awaiter(this, void 0, void 0, function () {
        var error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 3, , 4]);
                    if (!connection) return [3 /*break*/, 2];
                    return [4 /*yield*/, connection.disconnect()];
                case 1:
                    _a.sent();
                    console.log('Disconnected from MongoDB');
                    _a.label = 2;
                case 2: return [3 /*break*/, 4];
                case 3:
                    error_2 = _a.sent();
                    console.error('Error disconnecting from MongoDB:', error_2);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    });
}
exports.disconnectFromDatabase = disconnectFromDatabase;
var fetchAndStoreMushroomData = function () { return __awaiter(void 0, void 0, void 0, function () {
    var mushrooms, error_3;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 3, , 4]);
                return [4 /*yield*/, axios_1["default"].get('https://example.com/api/mushrooms')];
            case 1:
                mushrooms = _a.sent();
                return [4 /*yield*/, MushroomModel_1["default"].insertMany(mushrooms.data)];
            case 2:
                _a.sent();
                console.log('Mushroom data fetched and stored successfully.');
                return [3 /*break*/, 4];
            case 3:
                error_3 = _a.sent();
                console.error('Error fetching and storing mushroom data:', error_3);
                return [3 /*break*/, 4];
            case 4: return [2 /*return*/];
        }
    });
}); };
exports.fetchAndStoreMushroomData = fetchAndStoreMushroomData;
var seedDatabase = function () { return __awaiter(void 0, void 0, void 0, function () {
    var seedData, createdUsers_1, createdMushrooms_1, updatedFavorites, error_4;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 10, 11, 13]);
                return [4 /*yield*/, connectToDatabase()];
            case 1:
                _a.sent();
                return [4 /*yield*/, BlogPostModel_1["default"].deleteMany({})];
            case 2:
                _a.sent();
                return [4 /*yield*/, FavoriteModel_1["default"].deleteMany({})];
            case 3:
                _a.sent();
                return [4 /*yield*/, MushroomModel_1["default"].deleteMany({})];
            case 4:
                _a.sent();
                return [4 /*yield*/, UserModel_1["default"].deleteMany({})];
            case 5:
                _a.sent();
                seedData = {
                    users: [
                        { name: 'Alice', email: 'alice@example.com', password: 'password123' },
                        { name: 'Bob', email: 'bob@example.com', password: 'securepassword' },
                    ],
                    mushrooms: [
                        {
                            scientificName: 'Agaricus bisporus',
                            commonName: 'Button Mushroom',
                            latitude: 40.7128,
                            longitude: -74.0060,
                            imageUrl: 'https://example.com/agaricus_bisporus.jpg',
                            description: 'A common edible mushroom.'
                        },
                        {
                            scientificName: 'Amanita muscaria',
                            commonName: 'Fly Agaric',
                            latitude: 51.5074,
                            longitude: 0.1278,
                            imageUrl: 'https://example.com/amanita_muscaria.jpg',
                            description: 'A poisonous mushroom with a red cap and white spots.'
                        },
                    ],
                    blogPosts: [
                        {
                            title: 'Mushroom Hunting Tips',
                            author: 'Alice',
                            content: 'Learn the basics of mushroom foraging...',
                            imageUrl: 'https://example.com/mushroom_hunting.jpg'
                        },
                        {
                            title: 'The Fascinating World of Fungi',
                            author: 'Bob',
                            content: 'Explore the diverse kingdom of fungi...',
                            imageUrl: 'https://example.com/fungi_world.jpg'
                        },
                    ],
                    favorites: [
                        { userId: '', mushroomId: '' },
                        { userId: '', mushroomId: '' },
                    ]
                };
                return [4 /*yield*/, UserModel_1["default"].create(seedData.users)];
            case 6:
                createdUsers_1 = _a.sent();
                return [4 /*yield*/, MushroomModel_1["default"].create(seedData.mushrooms)];
            case 7:
                createdMushrooms_1 = _a.sent();
                updatedFavorites = seedData.favorites.map(function (favorite) { return (__assign(__assign({}, favorite), { userId: createdUsers_1.find(function (user) { return user.name === 'Alice'; })._id, mushroomId: createdMushrooms_1[0]._id })); });
                return [4 /*yield*/, FavoriteModel_1["default"].create(updatedFavorites)];
            case 8:
                _a.sent();
                return [4 /*yield*/, BlogPostModel_1["default"].create(seedData.blogPosts)];
            case 9:
                _a.sent();
                console.log('Database seeded successfully.');
                return [3 /*break*/, 13];
            case 10:
                error_4 = _a.sent();
                console.error('Error seeding database:', error_4);
                return [3 /*break*/, 13];
            case 11: return [4 /*yield*/, disconnectFromDatabase()];
            case 12:
                _a.sent();
                return [7 /*endfinally*/];
            case 13: return [2 /*return*/];
        }
    });
}); };
exports.seedDatabase = seedDatabase;
