var cache = [];

$(document).ready(function() {
    
    // aux functions 

    var display_group_name = function(name) {
        return name == '__ALL__' ? 'Uncategorized' : name;
    }

    var render_group = function(g) {
        var container = $('<div>').addClass('clear');
        var node = $('<a>').attr({href: 'javascript:;', groupname:g.name}).addClass('groupclosed').click(function(e) {
            open_group($(this));
            e.stopPropagation();
            e.preventDefault();
        });
        var span = $('<span>').text(display_group_name(g.name));
        container.droppable({accept: '.userinfo_pic', drop: function(event, ui) {
            var src  = ui.draggable;
            var dest = $('a', this).attr('groupname');
            move_user(src.get(0).id.substring(5), dest);
        }});
        $('#groups').append(container.append(node.append(span)));
    };

    var render_user = function(u) {
        var container   = $('<li class="userinfo green' + ($(':radio[name=viewstyle]:checked').val() == 's' ? ' short_details' : '') + '">');
        var picture     = $('<div class="userinfo_pic" id="user_' + u.screen_name + '">')
            .append('<img src="' + u.profile_image_url + '" alt="' + u.screen_name + '" width="48" height="48"/>')
            .draggable({appendTo : 'body',helper:'clone'});
        var screen_name = $('<div class="userinfo_screenname">').html('<a href="http://twitter.com/' + u.screen_name + '" target="_new">' + u.screen_name + '</a>');
        var controls = $('<a href="javascript:;">[<-->]</a>').click(function(e) {
            $('#user-to-move').val(u.screen_name);
            $('#user-to-move-name').text(u.real_name);
            var groups = $('#group-to-move');
            groups.empty();
            for (var g in cache) {
                if (g != $('#info_groupname').text()) {
                    groups.append($('<option>').attr('value', g).text(display_group_name(g)));
                }
            }
            $('#move-dialog').dialog('open');
            e.stopPropagation();
            e.preventDefault();
        });
        container.append(picture).append(screen_name);
        if (u.real_name && u.real_name != '')
            container.append($('<div>').addClass('userinfo_realname').text(u.real_name));
        container.append(controls);
        $('#groupmembers ul').append(container);
    }

    var open_page = function(id) {
        if (id != 'manage' || phalanges.api.token) {
            $('.menu').removeClass('active');
            $('#m' + id).addClass('active');
            $('.page').hide();
            var p = $('#' + id);
            if (id != 'manage')
               p.load(id + '.html');
            p.show();
        }
        else {
            $('#login-dialog').dialog('open');
        }
    };

    var move_user = function(screen_name, group_name) {
        phalanges.api.move_friend(screen_name, group_name, function(results) {
            var src = null;
            var destg = null;
            var srcg = null;
            for (var g in cache) {
                var info = cache[g];
                for (var i = 0; i < info.users.length; i++) {
                    if (info.users[i].screen_name == screen_name) {
                        src = info.users[i];
                        srcg = info;
                        info.users.splice(i, 1);
                        break;
                    }
                }
                if (info.name == group_name) {
                    destg = info;
                }
            }
            if (destg && src) {
                destg.users.push(src);
                if (destg.name != srcg.name)
                    $('#user_' + screen_name).parent().remove();
            }});
    };

    var delete_group = function(name) {
        $('#group-to-delete').val(name);
        $('#group-to-delete-name').text(name);
        $('#delete-confirm-dialog').dialog('open');
    }

    var create_group = function(name) {
        phalanges.api.new_group(name, function(results) {
            var g = {name: name, users: [], rssurl: results.rssurl};
            cache[name] = g;
            render_group(g);
        });
    }

    var rename_group = function(old_name, new_name) {
        phalanges.api.rename_group(old_name, new_name, function(results) {
            var tmp = [];
            for (var g in cache) {
                var info = cache[g];
                if (info.name == old_name) {
                    info.name = new_name;
                }
                tmp[info.name] = info;
            }
            cache = tmp;
            $('#groups a').each(function() {
                var o = $(this);
                if (o.attr('groupname') == old_name) {
                    o.attr('groupname', new_name);
                    $('span', o).text(new_name);
                    open_group(o);
                }
            });
        });
    }

    var open_group = function(e) {
        $('#groups a').removeClass('groupopen').addClass('groupclosed');
        e.removeClass('groupclosed').addClass('groupopen');

        var g = cache[e.attr('groupname')];
        $('#info_groupname').text(display_group_name(g.name));
        $('#info_groupfeed').attr('href', g.rssurl);

        $('#delete-group').unbind('click').click(function(e) {
            delete_group(g.name);
            e.stopPropagation();
            e.preventDefault();
        });

        $('#rename-group').unbind('click').click(function(e) {
            rename_group(g.name, 'new ' + g.name);
            e.stopPropagation();
            e.preventDefault();
        });


        $('#groupmembers ul').empty();
        for (var i = 0; i< g.users.length; i++) {
            render_user(g.users[i]);    
        }
    }

    var do_login = function() {
        $('.error').hide();

        var screen_name = jQuery.trim($('#screen_name').val());
        var password    = jQuery.trim($('#password').val());

        if (screen_name == '')
            $('#ename').show();

        if (password == '')
            $('#epass').show();

        if (screen_name == '' || password == '')
            return;

        phalanges.api.login(screen_name, password, function() {
            $('#login-dialog').dialog('close');
            $('#currentuser').html(screen_name);
            $('#currentuserurl').attr('href', 'http://twitter.com/' + screen_name);
            $('#loggedin').show();
            $('#loggedout').hide();

            phalanges.api.get_friends(function(results) {

                var groups = [];
                for (var g in results) {
                    groups.push(results[g]);
                }

                groups.sort(function(a, b) {
                    if (a.name == '__ALL__')
                        return -1;
                    var k1 = a.name.toLowerCase();
                    var k2 = b.name.toLowerCase();
                    return k1 > k2 ? 1 : k1 == k2 ? 0 : - 1;
                });
                cache = [];

                $('#groups').empty();
                for (var i = 0; i < groups.length; i++) {
                    var group = groups[i];
                    render_group(group);
                    cache[group.name] = group;
                }
                open_group($('#groups a[groupname=__ALL__]'));
                open_page('manage');
            }, function(error) {
                open_page('manage');
            });
        },  function() {
            $('#eauth').show();
        });
    };

    // UI initialization
    $('#login-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#login-dialog').dialog('close');
            },
            'Login': function() {
                do_login();                        
            },
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Login to Phalanges',
        width: 350,
        open: function() {
            setTimeout(function() {$('#screen_name').focus()}, 100);
        },
        close: function() {
            $('#screen_name').val('');
            $('#password').val('');
        }
    });

    $('#delete-confirm-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#delete-confirm-dialog').dialog('close');
            },
            'OK': function() {
                var name = $('#group-to-delete').val();
                phalanges.api.delete_group(name, function(results) {
                    var src = cache[name];
                    for (var i = 0; i < src.users.length; i++)
                        cache['__ALL__'].users.push(src.users[i]);                        

                    var tmp = [];
                    for (var g in cache) {
                        var info = cache[g];
                        if (g.name != name)
                            tmp[g] = info;                
                    }
                    cache = tmp;
                    $('#groups a').each(function() {
                        var o = $(this);
                        if (o.attr('groupname') == name) {
                            o.remove();
                        }
                    });
                    open_group($('#groups a[groupname=__ALL__]'));
                });
                $('#delete-confirm-dialog').dialog('close');
            },
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Please confirm group deletion',
        width: 350
    });

    $('#move-dialog').dialog({
        buttons: {
            'Cancel': function() {
                $('#move-dialog').dialog('close');
            },
            'OK': function() {
                var screen_name = $('#user-to-move').val();
                var group_name  = $('#group-to-move').val();
                move_user(screen_name, group_name);
                $('#move-dialog').dialog('close');
            }
        },
        autoOpen: false,
        modal: true,
        resizable: false,
        title: 'Please select destination',
        width: 350
    });


    // handlers

    $('#groups a').click(function(e) {
        $(this).toggleClass('groupopen').toggleClass('groupclosed');
        e.stopPropagation();
        e.preventDefault();
    });

    $('.menu').click(function(e) {
        var pageid = this.id.substring(1);
        open_page(pageid);
        e.stopPropagation();
        e.preventDefault();
    });

    $('#logoutbutton').click(function(e) {
        $('#loggedin').hide();
        $('#loggedout').show();
        phalanges.api.token = null;
        cache = [];
        open_page('about');
        e.stopPropagation();
        e.preventDefault();
    });

    $('#loginbutton').click(function(e) {
        $('#login-dialog').dialog('open');
        e.stopPropagation();
        e.preventDefault();
    });

    $('#screen_name,#password').keypress(function(e) {
        if (e.which == 13) {
            do_login();
            e.preventDefault();
            e.stopPropagation();
        }
    });

    $(':radio[name=viewstyle]').click(function() {
        if (this.value == 's')
            $('.userinfo').addClass('short_details');
        else
            $('.userinfo').removeClass('short_details');
    });

    open_page('about');



});
