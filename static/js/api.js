var phalanges = {
    api: {

        ERR_HTTP:           0,
        ERR_TIMEOUT:        1,
        ERR_PARSE:          2,
        ERR_INTERNAL:       3,
        ERR_AUTH_REQUIRED:  101,

        endpoint: '/mockapi',
        seqid: 0,

        token: null,

        login: function(screen_name, password, success, error) {
            this.jsonrpc('login', 
                {
                    screen_name: screen_name, 
                    password: password
                }, 

                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    phalanges.api.token = o.result.auth_token;
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        get_friends: function(success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('get_friends', 
                {
                    auth_token: this.token
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        move_friend: function(screen_name, group_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('move_friend', 
                {
                    auth_token: this.token,
                    screen_name: screen_name,
                    group_name: group_name
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        new_group: function(group_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('new_group', 
                {
                    auth_token: this.token,
                    group_name: group_name
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        rename_group: function(old_group_name, new_group_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('rename_group', 
                {
                    auth_token: this.token,
                    old_group_name: old_group_name,
                    new_group_name: new_group_name
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        delete_group: function(group_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('delete_group', 
                {
                    auth_token: this.token,
                    group_name: group_name
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        get_user_info: function(screen_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('get_user_info', 
                {
                    auth_token: this.token,
                    screen_name: screen_name
                }, 
                function(o) {
                    if (phalanges.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    phalanges.api.handle_request_error(o, status, thrown, error);
                });
        },

        jsonrpc: function(method, parameters, success, error) {

            var request = {
                method: method,
                params: parameters,
                id: ++this.seqid
            };

            $.ajax({
                contentType: 'application/json',
                data: $.toJSON(request),
                dataType: 'json',
                error: error,
                success: success,
                type: 'POST',
                url: this.endpoint
            });
        },

        handle_request_error: function(o, status, thrown, callback) {
            if (!callback)
                return;
            if (status == 'timeout')
                callback({code:this.ERR_TIMEOUT, message:'Timeouted'});
            else
            if (status == 'error')
                callback({code:this.ERR_HTTP, message:'HTTP error'});
            else
            if (status == 'parseerror')
                callback({code:this.ERR_PARSE, message:'Unexpected content'});
            else
                callback({code:this.ERR_INTERNAL,message:'Internal server error'});
        },

        handle_jsonrpc_error: function(o, callback) {
            if (o.error) {
                if (callback)
                    callback(o.error);
                return true;
            }
            return false;
        }


    }
};