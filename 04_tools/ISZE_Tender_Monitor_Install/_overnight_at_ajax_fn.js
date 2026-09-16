
          clearTimeout(pendingTableRequest);
          const wait = waitTimeToNextRequest(getNumberFromLocalStorage(LOCAL_STORAGE_LAST_PAGINATION), RATE_LIMIT_PAGINATION);

          data.orderColumn = data.order[0]?.column;
          data.orderDir = data.order[0]?.dir;
          data.kdTypes = [];
          $("input:checked[id^='kdt']").each(function () {
            data.kdTypes.push($(this).attr("value"));
          });
          data.cpvList = [];
          $("input:checked[id^='cpv']").each(function () {
            data.cpvList.push($(this).attr("value"));
          });
          data.kdBaseTypes = [];
          $("input:checked[id^='kdbt']").each(function () {
            data.kdBaseTypes.push($(this).attr("value"));
          });
          data.eFormsBaseTypes = [];
          $("input:checked[id^='efbt']").each(function () {
            data.eFormsBaseTypes.push($(this).attr("value"));
          });
          data.nutsList = [];
          $("input:checked[id^='nt']").each(function () {
            data.nutsList.push($(this).attr("value"));
          });
          data.q = null
          data.fromdate = null
          data.todate = null

          pendingTableRequest = setTimeout(() => {
            writeNumberToLocalStorage(LOCAL_STORAGE_LAST_PAGINATION, String(Date.now()));
            $.ajax({
              url: "\/at.gv.bmdw.eproc-p\/public\/api\/tenderlist",
              contentType: "application/json; charset=utf-8",
              data: data,
              dataType: "json",
              success: function (json) {
                callback(json);
              }
            });
          }, wait);
        },
        drawCallback: function (settings) {
          $('#tenderlist_paginate ul.pagination').attr('aria-label', 'Paginierung');
          $('#tenderlist th').each(function () {
            const th = $(this);
            const ariaLabel = th.attr('aria-label');
            th.removeAttr('aria-label');
            th.children('span').attr('aria-label', ariaLabel);
          });
          const inputCaller = $("input[name=callerId]");
          const callerId = inputCaller.val();
          if (callerId.trim() === "") {
            $('#tenderlist_wrapper table tbody tr:eq(0) td:eq(0) a').focus();
          } else {
            inputCaller.val('')
            $("#" + callerId).focus();
          }
          $('.dt-paging nav').attr('aria-label', 'paginierung');
        },
        "language": {
          "url": "\/at.gv.bmdw.eproc-p\/json\/datatables-info-d4464a047a9f487a30251e7b1b4992e5.json"
        