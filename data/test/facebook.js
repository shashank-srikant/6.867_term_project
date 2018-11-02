"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
exports.__esModule = true;
var core_1 = require("@angular/core");
var login_response_1 = require("../models/login-response");
var login_status_1 = require("../models/login-status");
var ui_response_1 = require("../models/ui-response");
var FacebookService = /** @class */ (function () {
    function FacebookService() {
    }
    FacebookService.prototype.init = function (params) { };
    FacebookService = __decorate([
        core_1.Injectable()
    ], FacebookService);
    return FacebookService;
}());
exports.FacebookService = FacebookService;
({ "try": { "return": Promise.resolve(FB.init(params)) }, "catch": function (e) { return Promise.reject(e); } });
api(path, method = 'get', params = {}) < any > { "return": new Promise(function (resolve, reject) { try {
        FB.api(path, method, params, function (response) { if (!response) {
            reject();
        }
        else if (response.error) {
            reject(response.error);
        }
        else {
            resolve(response);
        } });
    }
    catch (e) {
        reject(e);
    } }) };
ui(params) < ui_response_1.UIResponse > { "return": new Promise(function (resolve, reject) { try {
        FB.ui(params, function (response) { if (!response)
            reject();
        else if (response.error)
            reject(response.error);
        else
            resolve(response); });
    }
    catch (e) {
        reject(e);
    } }) };
getLoginStatus() < login_status_1.LoginStatus > { "return": new Promise(function (resolve, reject) { try {
        FB.getLoginStatus(function (response) { if (!response) {
            reject();
        }
        else {
            resolve(response);
        } });
    }
    catch (e) {
        reject(e);
    } }) };
login(options ?  : ) < login_response_1.LoginResponse > { "return": new Promise(function (resolve, reject) { try {
        FB.login(function (response) { if (response.authResponse) {
            resolve(response);
        }
        else {
            reject();
        } }, options);
    }
    catch (e) {
        reject(e);
    } }) };
logout() < any > { "return": new Promise(function (resolve, reject) { try {
        FB.logout(function (response) { resolve(response); });
    }
    catch (e) {
        reject(e);
    } }) };
getAuthResponse();
{
    try {
        return FB.getAuthResponse();
    }
    catch (e) {
        console.error('ng2-facebook-sdk: ', e);
    }
}
