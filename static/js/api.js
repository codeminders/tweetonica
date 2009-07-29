var tweetonica = {
    api: {

        ERR_HTTP:           0,
        ERR_TIMEOUT:        1,
        ERR_PARSE:          2,
        ERR_INTERNAL:       3,
        ERR_AUTH_REQUIRED:  101,

        endpoint: '/api',
        seqid: 0,

        token: null,

        get_prefs : function(success, error) {
            this.jsonrpc('get_prefs', 
                {
                    auth_token: this.token
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        set_prefs : function(prefs, success, error) {
            this.jsonrpc('set_prefs', 
                {
                    auth_token: this.token,
                    prefs: prefs
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        sync_friends: function(force, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('sync_friends', 
                {
                    auth_token: this.token,
                    force: force
                }, 
                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        create_friendship: function(screen_name, success, error) {
            if (!this.token) {
                if (error) {
                    error({code: this.ERR_AUTH_REQUIRED, message: 'Authentication is required'});
                }
                return;
            }
            this.jsonrpc('create_friendship', 
                {
                    auth_token: this.token,
                    screen_name: screen_name
                }, 
                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        reset_RSS_token : function(success, error) {
            this.jsonrpc('reset_RSS_token', 
                {
                    auth_token: this.token
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        get_feed : function(group_name, offset, success, error) {
            this.jsonrpc('get_feed', 
                {
                    auth_token: this.token,
                    group_name: group_name,
                    offset: offset
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        post_tweet : function(message, in_reply_to, success, error) {
            this.jsonrpc('post_tweet', 
                {
                    auth_token: this.token,
                    message: message,
                    in_reply_to: in_reply_to
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
                });
        },

        post_direct_tweet : function(to, message, success, error) {
            this.jsonrpc('post_direct_tweet', 
                {
                    auth_token: this.token,
                    to: to,
                    message: message
                }, 

                function(o) {
                    if (tweetonica.api.handle_jsonrpc_error(o, error)) {
                        return;
                    }
                    if (success)                    
                        success(o.result);
                }, 
                function(o, status, thrown) {
                    tweetonica.api.handle_request_error(o, status, thrown, error);
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