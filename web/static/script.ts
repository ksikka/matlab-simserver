//import _ = require('lodash');
interface SimResult {
  result:any;
  out:string;
  err:string;
  has_error:boolean;// if true, then result is string or list of strings representing traceback.
}

interface SimResultCB {
  (a: SimResult): void;
}

var nl2br = function(str : string) {
  return str.replace(/ /g, '&nbsp;').replace(/(?:\r\n|\r|\n)/g, '<br />');
};

var inflateSimResult : ((Object) => SimResult) = function(data) {
  var obj = {
    result: data[0],
    out: data[1],
    err: data[2],
    has_error: (data[3] !== undefined)
  };
  return obj;
};

declare var backendDown;
_.templateSettings.imports['backendDown'] = backendDown;

var simDetail = _.template($('#sim-detail-template').html());
var replLineHtml = $('#repl-template').html();
var simDetailCurrentState = _.template($('#sim-detail-current-state-template').html());

var renderSimResult = function(data, $simRDiv) {
  var simr = inflateSimResult(data);
  var resultStr = typeof(simr.result) === "string" ? simr.result : JSON.stringify(simr.result, null, 2);
  var newHtml = simDetailCurrentState({
    status: {loaded:true},
    result: nl2br(resultStr),
    out: nl2br(simr.out),
    err: nl2br(simr.err),
    has_error: simr.has_error,
  });
  $simRDiv.html(newHtml);
};

var getState = function(uuid) {
  return $.post('/sim/'+uuid+'/feval/', {fn_name: 'sim.getState'});
};
var simEval = function(uuid, statement, nargout) {
  return $.post('/sim/'+uuid+'/eval/', {statement: statement, nargout: nargout});
};
var simDelete = function(uuid) {
  return $.post('/sim/'+uuid+'/delete/');
};

var newSim = function (simtype, params, description) {
  var reqData = { simType: simtype,
               paramsJson: JSON.stringify(params),
               description: description };
  return $.post('/sim/create/', reqData);
};


// fix the form to use the AJAX URL. we do it in JS so that if no-JS then old URL is still there.
$('document').ready(function() {
    $('form.sim-new').attr('action', '/sim/create/');
});

$('.btn.sync-users').click(function (e) {
  e.preventDefault();
  var options = {
    error: function(jqXHR, textStatus, errorThrown) {
      alert(errorThrown);
    },
    success: function() {
      alert('done');
    }
  };
  $('form.sync-users').ajaxSubmit(options);
});
$('.btn.sim-new').click(function (e) {
  e.preventDefault();
  $('form.sim-new').toggleClass('hidden');

});


// the only point of ajaxing this is to show the loading wheel
$('form.sim-new').on('click', 'input[type="submit"]', function(e) {
  e.preventDefault();
  $('.ajax-loader').toggleClass('hidden');


  var $submitBtn = $(this);
  $submitBtn.attr('disabled', 'disabled');

  var options = {
    error: function(jqXHR, textStatus, errorThrown) {
      alert(errorThrown);
    },
    success: function() {
      location.reload();
    },
    complete: function(data, jqXHR) {
      $submitBtn.removeAttr('disabled');
      $('.ajax-loader').toggleClass('hidden');
    }
  };
  $('form.sim-new').ajaxSubmit(options);


});



$('tr.simulation').click(function (e) {
  e.preventDefault();
  var uuid = $(this).data('uuid');
  var simOpenCloseDiv = $(this).next().find('td > div').first();
  var simContentDiv = $(this).next().find('.content');
  // this wont work the first time, see the other place where it gets set
  var simContentCurrentStateDiv = simContentDiv.find('.current-state');
  var simContentActionsDiv = simContentDiv.find('.actions');

  var opening = simOpenCloseDiv.hasClass('closed');
  simOpenCloseDiv.toggleClass('closed');
  if (opening) {
    var simTrDiv = this;
    if (simContentDiv.html() == '') {
      var params = $(this).next().find('.params-json').text();

      var newHtml = simDetail({
        simId: uuid,
        params: nl2br(params)
      });
      simContentDiv.html(newHtml);

      simContentCurrentStateDiv = simContentDiv.find('.current-state');

      simContentActionsDiv = simContentDiv.find('.actions');
      simContentActionsDiv.html(replLineHtml);
      var submitRepl = function($replLine) {
        $replLine.find('input').prop('disabled', true);
        var statement = $replLine.find('input.statement').val();
        var nargout = $replLine.find('input.nargout').val();

        var $simRDiv = $('<div class="sim-result">Loading...</div>');
        $replLine.after($simRDiv);

        simEval(uuid, statement, nargout)
          .done(function(data) {
            renderSimResult(data, $simRDiv);
            var $nextReplLine = $(replLineHtml);
            $simRDiv.after($nextReplLine);
            bindReplEvents($nextReplLine);
          });
      };
      var bindReplEvents = function($replLine) {
        $replLine.find('input').keyup(function(e) {
          if (e.keyCode === 13) {
            submitRepl($replLine);
          }
        });
      };
      bindReplEvents(simContentActionsDiv.find('.repl-line'));

      simContentDiv.find('.sim-delete-btn').click(function(e) {
        if (backendDown) {
          $(this).text('Service Unavailable :-(');
          return;
        }
        e.preventDefault();
        simDelete(uuid).fail(function() {
          alert('Error while deleting sim '+uuid+'. Please refresh.');
        });
        simOpenCloseDiv.toggleClass('closed');
        // when transition finishes, get rid of the row in the table.
        window.setTimeout(function() {
          $(simTrDiv).remove();
        }, 550);
      });

    }


    getState(uuid)
      .done(function(data) {
        var simr = inflateSimResult(data);
        var resultStr = typeof(simr.result) === "string" ? simr.result : JSON.stringify(simr.result, null, 2);
        var newHtml = simDetailCurrentState({
          status: {loaded:true},
          result: nl2br(resultStr),
          out: nl2br(simr.out),
          err: nl2br(simr.err),
          has_error: simr.has_error,
        });
        simContentCurrentStateDiv.html(newHtml);

      })
      .fail(function() {
        var newHtml = simDetailCurrentState({
          simId: uuid,
          status: {backendDown:true},
        });
        simContentCurrentStateDiv.html(newHtml);
      });

  }

});

