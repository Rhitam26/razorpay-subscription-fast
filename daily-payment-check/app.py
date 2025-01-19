import requests
import boto3
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
import json
from jinja2 import Template
from pydantic import BaseModel


load_dotenv()

razorpay_url = os.getenv('RAZORPAY_URL')
invoice_creation_url = os.getenv('INVOICE_CREATION_URL')
# invoice_creation_url = 'http://127.0.0.1:3030/generate-pdf'

AWS_ACCESS_KEY=os.getenv("ACCESS_KEY")
AWS_SECRET_KEY=os.getenv("SECRET_KEY")
AWS_REGION=os.getenv("REGION")

ses_client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)


class EmailContent(BaseModel):
    EmailAddress: str
    message: str = "Hello, This is a test message"

class EmailData(BaseModel):
    email_content: EmailContent
    email_json: dict


html_template ="""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      background-color: #f5f5f2;
      padding: 40px 20px;
    }

    .top-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 48px;
      width: 464px;
      justify-content: center;
    }

    .logo-image {
      height: 24px;
      width: auto;
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .logo-image.loaded {
      opacity: 1;
    }

    .company-name {
      font-size: 16px;
      color: #333;
      margin-left: 4px;
      font-weight: 400;
    }

    .receipt-container {
      background: white;
      border-radius: 16px;
      padding: 32px;
      width: 464px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
      margin-bottom: 16px;
    }

    .details-container {
      background: white;
      border-radius: 16px;
      padding: 32px;
      width: 464px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .container-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
    }

    .receipt-icon {
      width: 20px;
      height: 24px;
      opacity: 0.15;
    }

    .header {
      text-align: left;
    }

    h2 {
      color: #666;
      font-weight: 400;
      font-size: 16px;
      margin: 0 0 8px 0;
    }

    .amount {
      font-size: 36px;
      font-weight: 700;
      margin-bottom: 8px;
      color: #111;
    }

    .date {
      color: #666;
      margin-bottom: 32px;
      font-size: 14px;
    }

    .download-section {
      margin-bottom: 32px;
    }

    .separator {
      border-bottom: 1px solid rgba(0, 0, 0, 0.08);
      margin-bottom: 32px;
    }

    .download-buttons {
      display: flex;
      gap: 24px;
    }

    .download-button {
      display: flex;
      align-items: center;
      color: #666;
      text-decoration: none;
      font-size: 14px;
      gap: 6px;
    }

    .download-arrow {
      color: #666;
      font-size: 14px;
    }

    .details {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
    }

    .detail-label {
      color: #666;
      font-size: 14px;
    }

    .detail-value {
      text-align: right;
      font-size: 14px;
      color: #111;
    }

    .details-header {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
    }

    .details-date {
      color: #666;
      font-size: 14px;
      margin-bottom: 32px;
    }

    .item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
    }

    .item-details {
      color: #666;
      font-size: 14px;
      margin-top: 4px;
    }

    .total {
      padding-top: 16px;
      border-top: 1px solid rgba(0, 0, 0, 0.08);
      display: flex;
      justify-content: space-between;
      font-weight: 500;
      margin-top: 24px;
    }

    .amount-cell {
      font-weight: 500;
    }
    .download-button {
      display: flex;
      align-items: center;
      color: #666;
      text-decoration: none;
      font-size: 14px;
      gap: 8px; /* Increased gap for better spacing */
      padding: 8px 12px; /* Added padding for better touch target */
      border-radius: 6px; /* Rounded corners */
      transition: background-color 0.2s ease; /* Smooth hover effect */
    }

    .download-button:hover {
      background-color: rgba(0, 0, 0, 0.05); /* Light background on hover */
    }

    .download-arrow {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      color: #666;
    }

    /* Arrow icon using CSS */
    .download-arrow::before {
      content: '';
      display: block;
      width: 8px;
      height: 8px;
      border: solid #666;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg) translateY(-2px);
    }

  </style>
</head>
<body>
  <!-- Base64 encoded SVG logo placeholder -->
  <div id="imageData" style="display: none;">
    data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA9wAAADqCAYAAABQm00wAAAACXBIWXMAABYlAAAWJQFJUiTwAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAACyDSURBVHgB7d3LleNG2ubxp3u0mF3rs6BDFkiyQKHd7FSyQJAFqrYg0atZqtoCUhZIWs4qKQtUsoCQBarPghy+B+RHMisvRATiBvx/58TJrMpMMkAAEfEibn8TAABYmy8OyR/S58fvPz0kJwAA1mc4pveH9Och7Y7fz+JvAgAAa+AP6ZtD6jQG2AAA4GmDxsD7P4oMvgm4AQBYNn9Id8evAABgGgu4LfDeKgABNwAAy+RFoA0AwFyGQ/r6+PVmfxcAAFgSGy7+4yHdi2AbAIC5uEPaa6xjb56aRQ83AADL4TQG2k4AACCVQTf2dhNwAwCwDLbauAXbLIgGAEB6HzQG3S8uqsaQcgAA2vfdIf0ugm0AAHKxOtfq3u9e+iV6uAEAaJv1bP8uAABQypd6pqebgBsAgHY50bMNAEBpNrzcgu7h8Q8IuAEAaNNpKJsTAAAobdAYdH+4/M//JQAA0KL/e0j/RwAAoAb2IPx/H9L/EwAAaJo7pIcZkq1q/lbjPHCGpQMA1sbqPq+xLrQ6cY661QsAADRtr7jGwEYMRQcA4DF3SFvFP8wGAACN6hTeCNhr7M0GAADPc4p7uO0FAACaZAulhVT+WzFsHACAW1md+bPo5QYAYDWsdzqk4v9ZAAAgxFb0cgMAsAobhQ0jp2cbAIAwVodaXTq1/n0nAADQlJAK3wkAAMQIGWH2lwAAQDNCKvuNAADAHLaaXg+zUCkAAI2wPULp3QYAoAyn6fXw278LAAC0wGma3SENAgAAcxg01q1TfE7ADQBAGz7XNL8KAADMaWrd+gUBNwAAbXCa5r0AAMCcdpqGXUIAAGjE1HljVPIAgCV7c0g/63oHj981LhjqlManml4fAwCABlDBAwAwrvxtgfVr9eCd0qA+BgBggajgAQBrZ8G27W99a134u+ZHfQwAwAJRwQMA1szpevj4relHzYv6GACABaKCBwCs2UbT68JT8poP9TEAAAtEBQ8AWKuQxcou0zvNZ9J7sy0YAAAAAKBmXnG+USEE3AAAAACAmjnFcSqEgBsAAAAAgAQIuAEAAAAANXuvOLF/H4yAGwAAAABQMwuYPyhcsYAbAAC0gVXKAQBr1it8lXKn+VAfAwCwQFTwAIA1s63B9ppeH/aaF/UxAAALRAUPAFi7O02rC7eaH/UxAAALRAUPAFgzd0h/6bY60H7vrdKgPgYAYIGo4AEAa7bXuY6z7/0hvTuke30caH+qdKiPAQBYICp4AMBa3em6jnMXP3O6DsRToz4GAGCBqOABAGvkdV2/9Y9+7kTADQAAIlHBAwDWxul6KPnPz/wOATcAAIhCBQ8AWJuNroNp98TvOBFwAwCASFTwAIA1+UHX9dqbZ37PiYAbAABEooIHAKyF0/UWYP0rv0vADQAAolDBAwDWwgLnW4NoN+F35zCpPv67AAAAAACow52u52p/LQAAgMTo4QYALJ3N076sy97e8DdODCkHAACRqOABAEvmdD2UfDPh7wi4AQBAFCp4AMCSWYB9GTi7G//OiYAbAABEooIHACzVrVuAPcWJgBsAAESiggcALJHTdf3VaxonAm6giE8P6YtD8sevANAyKngAwBJZkBwTMLvIv5+K+hirZkH2na5v3Mv0s8YAHABaQwUPAFgaa7ef6q2/dPu87UtOBNxAFjb3w27UWy78jcbgHABaQQUPAFiSTtf11i1bgD3FiYAbSO5O0y/+30XQDaAdVPAAgKVwCtsC7LnXIuAGErrT9Av/lO4FAG2gggcALIVN87wMkp3CORFwC0jFKTzYjh2+AgA5UcEDAJbgTtf1lVccJwJuIJmN4gNum/fN0HIAtaOCBwC0zum6ruoVz4mAG0jCguSHmVInAKgbFTwAoHUWEM8dHLsEr/mSSfXx3wW0a869tdmnGwAAAEjnR53nan84pK+1AgTcaNmcQbITAAAAgBQ6Xa+b9O9DGrQCBNxo2Zzzrv8hAAAAAHNzGhdKO9ke0jutxCcC2vVBAAAs25tD+kZ5/HpIvwgIYx0hPyoPawP+S2jFRufRpIPG3m0ADbBGyFyLpq3mKRuAZk0t17AMvear615LvYBwTvmu1b3Qijtdnzuv+TmxaBqQxE7zeS8AAAAAc3G6fpBnPds7rQwBN1pmw4l2ijdohTc/AAAAkIhNMbi/+PeglY6iIeBG6+aYA/KTVrJKIgAAAJCBDSV3x+9XswXYUwi40bqd4oLuQcxZAwAAAObS6XoLMFvgbtBKEXBjCXqNvdRTDVrx0zYAAABgZk4fbwG21YoRcGMpOk3r6d5pDLYHAQAAAJjDRmwBdoWAG0vSH9JnGnu7n9uje3dI34tgGwAAAJiT9Wz7i39/K9rb+kTAsgwae7uN17hCoiULwN+Lmx4AAACYm9PHW4Cx7a4IuLFsOwEAAABIiS3AXsCQcgAAAABAKLYAewEBNwAAAAAgRCe2AHsRATcAAAAAYContgB7FQE3AAAAAGCqx1uA/Uv4CAE3AAAAAGCKx1uA2bztD8JHCLgBAAAAALdy+ngLsEF4EgE3AAAAAOAWj7cAs722e+FZBNwAAAAAgFv8qOt5298KLyLgBgAAAAC8pjumE4aS3+ATAQAA1MlpHL74qc49Kk/5cJEGsXAPbne6ttzx+6cM4toCnNgCLAgBN0pxF98PQgmnRuxjp0brkrln/n8QgBKsLPKH9JXG+/MLPV9G3crmFQ6H9Mch7Y7/rqVsm3Js/1A+9l5O8QbV6fI6+0Ln62wKu4bsWvpN43W1UzynfAZN52b+vbk4xVtDm2cuP4stwIL8TctwejppBefnun5S+VSl9vgpuFXGp4r5vTAX+9xPFdrnOlds7tHv2TYCOyEV+8zf6Hxv3NqQHXS+J/48ft2pHU9df06vH/epbLB0Kht2okKewmls1NrXf+pcJktPN5AGXZfLp8+9pgCpBg+apvY63h/SNxrLJ6c8dof06yH9orJBodf1okNL85nqCbqtzO80Xmte87Myyq6n03UVYuq9HSOkXNgrfzCdy/aQvhdeYz3b/cW/a7rHjdN4nZpBY/5SmnTPhtx07xT2tDWmIHqK1/iE0r6GPKF8zunJpeV3p7YD8I3C/KTwwCqkYosNuO09f1SY1HNP7Nr8QWHsyWFosOGVriG70/kaGVSXy+tvznLBnALvU9mAM6fxWjuVyXN+7oOuP/e5AnDL7zcKU6pxtoSA22v83DvNe52EsHv6PypTlnkRcKfm9fE+wakNGtsVO007fgLucrYi4H6N0zmYNXaN96qLU8UBd4j98U2mpl7xrHK2wvOvwDyEJDvet2qzoAk95k7TeY2Nh5D384rjFH6sXml5hefNaZrT/fF7xHtOTfcKu17m5hV+/YWWC3dabgPkFna9WdmY83O3ZEPa3iheH5GHUlrJ51O88l8rU+7njfLez151fhZzJadyvMpfa3tNqxtz5i3EPmP+cqeN8BKn6/N/rzo5Xd9/qSW/7/YKu6B7hfOqo6LeKO+T0lihx9npdl7x58Yrjiv43q/xCs+bu/E9SjyIepz2Gnvyc/dYdcr7gOG5csFpPbzGYy55vZ2uuU7h+oj3LqWVfF7yqjfQfpzsmr5THl5tfCahySk/p/qutb1ua2fkzFOIfcb85U4b4SX2+Vxez051crrOZ2rJ77u9wi7oXtM51VlR36uNBnbo8XU3vLbTfOfGK44r+N6v8QrPm7vh9S3ILR34XKa98vR4e9VXNmy07MDbq87yeK+wa66PeM9SWsmnOU31qeU6mXpNfaG0vKSHBSenvO5U9+fx2rS3nHkJsc+UtxJpo3i3rIvTok7Xn1Wnejmd87lXesnvu73CLuhetzv12D1Unjaqu4EdelzdK6/7neYN8rziuILv/Rqv8Ly5F17XfnYf8dqp015p7g0rGzZSlmMIPe5Oy1L7Zx56zfUR71VKK/n0WkYD/U7peEkPC05OeTiVH+V0a9rr+c8lZz5C7DPmL3faKIzX+CBl/+j17rWMdoDTdVv/nepzObXtMq/2vZ1Xp3SS33d7hV3Q/Y2v79XWjW15fas6hR5T98Jrpuix8IrjCr73a7zC8+aeeU2bv1pTr/ZL6U7z8WqnbNhoGb3dtY2gmPOa6yPeo5QW8nmn+q6JmGRrBqToufKSHhacnNL7Tu2VT3s9PXoiZx5C7DPmL3faaJpbR+/slX6kTEqW/8tjqa0H3+u269LOb4q8T73OJrvl4J5K/Q2v3erwM0v3qq+BHXos3TOvt4l4zZeSVxxX8L1f4xWeN/fE691FvF6pZPd1bGH3g9LmMUXaq92g286XBRqtfNYhn30f8fql1J7Pjeq7FnJdT1N5KUveSyWntO4kPTSa7CHB40As5/uH2GfKW4m00e2sbpw6ouI7tedO18fgVBfreJpyDuyczR10T73OJtsHvIml/oXXtA/hPvB1a0p71bWoWuhxdE+81ibi9V5LXnFcwfd+jVd43tyj17qLeK3S6XeFF9h3GfKXKu3V3hNuy6/lu4XPN+az7yNeu5Sa87lRXec/xfXkNB8vZcl3qeSUzp2kh8bT46A753uH2GfKW4m00e02Aa9v59qpHXZdXua/V12cwka2TDnPt5j6/pPtA97kpRPmtLwb+U51CM1/9+h1Uo888IrjCr73a7zC8+YuXucu4nVqSXtNf8J4lzmPKdJTvRm1+k7tDdF8LX33zLH2Ea9ZSq35bHl02pS013wNZy9lyXOp5JTGnaSHhaS9zp9TzvcNsc+Yv9xpo9v4iPe4Vxuc6t8CzM5X6Hnwms+k9/5EZTm1s+L3FP3x67/VvjvVO0d9LWw4da/2OY33+9eH9OGG37drr1f7TiN4vjykQfWy66zGRVFibTVee0soj2u0pjrCaZxqcWsZhnktpU44cRqvpy+FFnyncF5tbCts7QB3/N7KuJ9UV76tPdUpnJ3DnRpx+eRjSuofvY7Tsp+YWbpTWaH57o5/7yNeY0ryiuMKvvdrvMLz5hR3bLWmjV7X4pzt19Je9T5cvFNbn2VI+u7RMfcRr1VKbfn0UvBn2HJ6bYunW3ilzWPp5DSvOylLvkukPvP7hdhnyluJtNFtWlkNn/R82ms+k967VA+30/w92/YkZjik94f03/r46bM9Ffnn8esXyrPaXn/82mLPitP88x0wzWnhqlh2L9h98YfO98lT7+UO6XOdA/1UumNenutNdZqvp/X9Mf2p53uXnc7HnXLot9N4T32tuuQcQXFZTps/H/08ZTm9Pb7fTpjDabu4NbIefbuWljgipEZey+rZfuxOaEHLK45j5FRIqYDbgginOKcg4tdD+kXTh2p+cUzfaCzMUwXgvcYHAK1VzJfDSlCG9aI4hdkp/N7Q8X29xl5Br/nZse10Drwu3SvcaQjUL8fXnjrs8xTodYf0ldKsTGyN9VrKgzdKmxf7/HeH9JvqKKdPwzcHIZYFCU7rZccfWr7idk48/McyDKq3vPAX35/iqxqd2mirYN3xId34/fHvYxdXsca4NVjnDpA7pV0p3Su/0LzeRfztc0M4bCjO/TFZo3dzkWJvHheRN6+0vBT9+U1JFjzNXRg5jb2Dc+f1/on3uot4La/5dUozlM6pPKd0C6TZ+bBgvsZy+nTd9RGvUUot+XQK/+yWlO4VzifMVw3JaR73Sp/XtaUQ+0x5K5E2uk3skHKvOt3pOp9O9fKKOwe/az5T33uyvcIOstfYWAr9kO6V52J1ShNclNgWICavMRezBX2d8h2vU3h+vdLyCs/blDTHqJHXOM1/b7x99PpT/36vPOVCp3kbHPcqywLhOY/n8ri80nOKuxbtuusj/r6UWvK5Ufhnt7TkFcYnzlfp5BRviWt51JBC7DPlrUTa6DZ9xHvsVSev63z2qpu1XWJilDlH9E1978n2CjvIHwP/1v7GKz+n+QuYe+X1kCnZxd+r3FMxp/C8e6XlJT0kTPbZv1Fenea7Nyz/p17QzcS/fac8azGcOI0PNuY6d17lzL2N073KHI9X2LVo190m4O9OqZQa8ukU/rktMd0rjM+Qt5LJKY7T8hfWLZVC7DPlrUTa6DYxwV6v+jhdn9c51gzKoVf4uXaaz9T3nmyvsIMM+bsa5jlaT8icwy7fKp+HxGmvuOX55+IUfgxeaXlJD4mSff5OZTjNVwH3mn4Oc95Hj/Wa7/yV0Gne67DkuTjpNe8xvZZKqSGfnaQH0lXyms5nylup5BRno7T5W3MKsc+UtxJpo9u9DXj9vfJ2DtzKjvsyj05tCB2h12teU99/spCDDLk4verhNG+PnlMeKc9R7t7FlziFH4dXWl7SQ4JkQ/dLf/5O89wXU3ob7Xe9yus1z3nMPTphzqHk9jo1LV7ilK9RWEoN+byX9FAo7XW9BsjPx/ykWovg1nSv6XymvJVKTuFcwnyRwuwz5a1E2miafsJr71VnIPt4ukantjhNuyZ7zW/qdTbZlAMMSbVenNZQnWsPvnvlkeL81BLwXHIKPx6vtLykh5nTXnU97LD8PGRKuQPUl/Rqpyw4udN816BTfZzy7JVaSul8firpIXOyoNrr9TLPKf3ipy+lqWWyz5i3Eskp3H3ivK09hdhnyluJtNF03Q2fib1ujT3bTtcPKWvZNWUqp9fXcrHjTDUKb+p1NtlrF1hMqqHX7jVbzXOsXunNfX72qreRXet58JIetOxz4JSnh6mGocuPbdVGWWCc5jkPayqnn0ullM6nl/SQKe0VtyDZPkMeY8onnzFvJZJTGJ84X6Qw+0x5K5E2CtdprG/2j16v5q2rLvO6V/ucxg6Q+4tk56BT2rbK1Otssr0UdWE/l+x1a2/EndjJjD3ee6U35/kpscr6rZzCj8srLS/pYcbkVCfreX5ImGp9AjvHEO1cx7aRos+DHatTG+Zc4O5xKqV0PkPmL4ZeZ7HtAfv7d0qf11O61zQ+Y95KJKcwmwx5W3sKsc+UtxJpo3jbi9frVK87XR+7E0JNus4+UR2GQ/pa42brLfhWYy+PUzh/TDu14V8azxPK+bfqPQe/HNJPh/Sd5jeo3q0qrMz6XnEP0OwzS9177xTfCBg0ltOD2mDnxanunobW5Pos52gP2N+f7qsflJ7XGOTfmu/3Go/zFp3SlK1PsXJ8q3iDpnOqM1ixc/Xb8eug62P79Jjs3vhKt01/aNH3N/6eHXuu1a7tXvtW8Qatg9d1W6rmNiWU5ilXiw0ip/hhtDGN9FvMdX5qn9/hFH5sXml5SXOcg73qF7s/4nOpU/22ijtGr7Q2UvR58GqPU5prspTS+byX9JA43Wt+OfJt6Y3S6KUs+X9Q2YebG+U7ztfSabvTkODZroOUI2xiU0pOUq7j2KseW53z1ak+Tm1uAVazSdfr31WePWF5r/YMGvMew6v+RuygdhdUWJLYay0He9r8H81rp3l6W1LrFccrHaf4BoBdfzu1Z9DtPTOow2+aX65rwAsxvMqzeszKu880lushIy1sxNe3x9cYBJR3p/Oo3EHjqFVkVDrgHlTvUNFbWCC6U5w71Y0hJ+UNaiPoNHM/nJk7gE9lUFxZ8JXS8YozqO1y+jTdAfFaHSo7KM814IRQXuU/v90hfanwQPuxQWPQ3cIDcyyXTanpLv7NFNECSgfct85fqpk9OY8pmG04fa2NmEHtBHpL1lJlbffCTvMYNAZLrYg5Tymn1cQ+1FtCY9Hm8rayRkjNctRVqd5jq/Q+F0J9p7Ls4W6qNSp6jYE8ZRByc/p43nZL7arFKBlwb7WMJyyD4nrhrHHRqU7clHXYqS1zBWit9G6f7BTeoLJywGl+PvJ1rQzYqn0ppjus0aD0UgWtO6UPeJyWuWBWDl7lWJ2VeuFKmzppQfcgIJ97ncukQW2PVmtayVXKlzTExobR2pCN0Ir2G9U5T5oGank7tVdBW8PCGraxDc8WH/jYsNXQFZGtl3vQvN4oDuU0LuXoofNKt4OH1Wn/FGpjZZ9TGVbG9cpj0Di3+zIIAlK5nLdtljCquFmlAu6tlvWU79R7Ejp002vadiI5nLa/QFm/qj12Hdv14xVuUJvXX8wCkE7zi5kbvlObC1o+J7achvTfymOjNMN7e6FGKafUvGSr/NeElak2FZFVopGSPWzvL/7NvO3CSg0pX+ICErG9cV51SbFSLKbbqU1/KM5ObYopB+YeSusU15Bd4kJj1svNPMpwg/Jwh/S72tgSEPG+UX6DyrVFrZ5gBCFScYf048W/t2K3oeJKBNw7LfMpiz213CmcV12Yv13eqae4RTvFafWBj52zQWH+S/PyCjdomQsmzrmo3xrlLI9s1Jf1dNvesZ0YgrtkTvmV3oGlFw//kMbjLcBYJb8CJQLuJW/PEjP8N+W2QCGWNJS0VS2fg9i8r/HY555bGjucfKnoWQq3U35OY+D91/GrDZUk+F4OO5e5h5QPKv9AkYUckQJbgFWqVA/3Um0VrqbtwT6IJ681GNSuQXFaDrhD57nOff/HNGJbXDvgVqdF/TBd6VE3nca5rxZ828JTb1Vu/i/mUeL81dLjxxQXzMnpeug4W4BVJHfAvdOyn7TEDCc1TnWgd7sOf6ptg8IMatugOsQ0ZHdarpanatSglocxXuM8RZvrbQG4BeJvVd/0LLwsd0fDoHqmy9DLjTndX3w/iEUiq5I74I5dSKkFMXNPa3lSPwg1GNS20Cf3g9o2KMycDc/YYHvpvS5L7sFP7Z3qY/eODTW3ANwanfSAtyP3+dmpLjsB8S7nbVv9zRZglSnRw710O4VzqkPrPatLMahtoUFbrq2HajNnwO0Ubg0PRunhDtfCwnN2L3mde8Bt4bXT/G/UxSmv2h627UQnB+J0uu7NLr0gIJ6QO+AetHwxDbm5F00KxZwizCH0OvpLbRtUnlO4QctHwB2ntVVvnc7zvx+OXzvV85B7zXK3e2q899mGFaGcxt7tk63YAqxKuQPuNTRyBoVzqgMBdx1aPw9r7amuQUxv+RrKaRaGjLNT23NPraf7tOWYDT3vxMrnpeT83GPX2UmFB4AIZaN43PH7QWwBVq2cAfdaCpSYhpwTcLbWgIApDfGcwg1ah0GI0WsZn6HXOfjeiEXXcssZcNfaDh0ETGc925fTZL4X11K1cgbcawoe6DkBUFLMMM1B6zAIMU4L8wxaBgv8Oo093ntd72WLdHIG3IPqRA83pnL6eN72TqhWzoB70HoMCsOQNgDIgykP8QYtK+g+cTr3endCSjnbPbXe83TSYCq2AGtM7jnceBkBN4CSBq0Hjdx5DFpm0G2cxsD7Xkz5WoJa73nKIkxxOW+bLcAakTPgXtO8TApPACXx8O51lNPzGbTcoNt4nRdXA4BSukN6e/FvtgBrBD3caTBUEUBJBNzIbTikL9X26uUvcRp7u+8EAPk5sQVYswi406hlP20AAHKxUQPW+7Lk1XJ7EXQDyM8e+Lnj94PYAqwpOQNuglAAyGMQUM5W4xDzpTYIexF0t6jWdigjkvAaK2/8xb/ZAqwx9HDXhTmFAEpyWg8npDRoDEw/O6SftLzGYa/ruZQIMyif/1KdnIDnObEFWPNyBty1FnQpOIUh4AYwh5iyZC29Lf8Qchg0LvRjgbf1yvyi5bDVgr3QCnq40Rq7NtgCbAEYUp6GU5hBABAvZuHGtTT+aOTmtz2kbzU+gD8F360/aP5Z9FDGGJSPU52+EPA0G0rujt+zBVjDcgbcTutAIw5AaYPCraXxRyO3HGs4bnUOvq0RacPO36s9Vuf/KITKuWWsnasa7/uvBHys0/W0lX+Jjrlm5Qy4P9U6gtGYwvwPAUC8QeGclm8t9VErdhobl7at2GnoeUvzvt+IoeWhco9w8KoPD//wmNPHW4BthWblXjRtDYVKzDEOAoB4MY3Yz7V8NHDrNWhsWHYag28LwlsIwFm1PMygvL5RXbyYkoCPsQXYwhBwzy+msToIAOLFDM3lwShqYtfyVucA/HLxtZrmf3sxaiLEoLy86jpP3wm49ngLMJt6MwhNyx1w1/ZkMQV6uAGUNig8GLEybOmBA3Mm2zXo6fnfg8rrhKlKzNt/qzo4MRUB15w+3gKsxbUt8EiJHu4lN+ScwgNuaxxzUwGYS0x54rVsXliKnc6936WD7zV0KsxtUP6RCj+ojrao9W47ASO2AFuw3AF3rStEzsUrHME2gDnFLMLotVxeDP1dqp2u9/welBdTFcLkbv/Y/V+6l9upnp521IEtwBYsd8Bt3mi5Yubi/CYAmM9O4ZY8r5A5k+uw1TnwztWDuvROhVRK7NBiwU3Jc2Xvz4M/nHRiC7BFKxFwW2NniYWMU1yv0E4AMJ+dwlkZ7bVMXliTrcaeolxBNwH3dL+oDFsJukR71ILtTsDIiS3AFu8T5WeFW3dI77QsMVuCWENgJwCYz6lc8Qpzp+WVS52YMzmV1dW55ibbFmApAmMbsvwf5dm6q/UOhRL5LzWlzh6O/KhxFEQu1unUC3NwWobHW4D9S1icEgG3sQUrlhRwO8X1mpR6ugtg2WyqilcYf0w7LQd7JYdxysMCoJ3SsDZHjvPv1LaYrU1DxT4cjNEdv+YIui3Y3mrZci+A59V2HfV4C7Cco3GQUYkh5cZpWcNpYleaZP42gBS2irOkALUTvdshcvY+plzjxRqxg9L7h+Y3KB+vMr3cv6qc7pB+VtrywTqatlq+EgF3q5w+3gJsEBapVMBtlrJghFPcwwMrnLYCgPkNinv677WcOc/0bofJGXCnXuNlEG5R4l7Zqix72GNbMnnNy65nG7a+tGmULxmUjz3IcGrP4y3ArJzthcUqGXA7LaMBdLmMfwiGkwNIKbbn6Ee1L7acXrNBeVf5fqt0Wl3QLPccZzsHudtnNaxl4zQGQZdzamN0h/S71rf9V85e7lPg6tQWq1fd8fvhkL4VFq1kwG2sEPJqV6f4ofH/FgCks1VcA8iClJYbjE70HMSwaydnwJdquyZ7zRyj6v5b8ysxp7M/pL3Gez/Xg4qSw8ovdRqP3QJvr2nsGru7+Hun9RmUl9P1+ap99Gyn69iBoeQrUGrRtEt2g6RamTQlp/gnwDtxkwFIy8rW2BWa7Wn8TuVWE45xL8SKWXwvhM2ntcWDBs3nB+WRoi0zHF83dyDhdD3C5YNuPz5baXnqCL6t6ppu2B3T6aGTpT90/Tk4jfm1xea8GElj/lQZna4D2UG32SnfSvVObAGGG9lTpIeZU4sNIhsmFHvcb5RWaL46tcUp/Fi90vIKz5tT27YKO+5ebfMKP+epfBqRp1Paq711NyxYeEiQSimVTyfpIXP6S/PVRXdSljxbSlWvz9HmyJk6hekT54uUXifpoaF0r3jbi9frXvi9y/t4r2WsZbVWk66z0kPKT7zamidoeY0dYjWI+dsA8jj1csdwGhsmrTQQ7rS+uZOpDMo/v9aus43ihuWeFqzqlc+gNNaym8k7sS1S63bCU6xOuowd2AJsRWoJuE2JRTpCzNWIyzV8BQBMr/jK3RoLLTwctXK6F+b0k8roNPYE2TBz6z2+5YGP13kebc6HLoPSTbtocTpHiDkeDqKsQQSSjzmxBdiq1TCH+1J//FrrQmLW0Jyj8t6KJ4AA8ppjLrfpNAY936vORhXBdhpbjXVgqREOb3Qerj1cpBPLl9N5Tm0JO6VjI+I2Wgfr5bY59wy3bZctgPedYJyuh63vRB21OjX1cJ/0KlupP+W07cBcT8pZmRxACdaQHRTvtGetU11yDx9em1rqLqexF7u7SHZN5lqJ/DkpRwHUsG1WLvRyt28nnNhDYHf8fhAjXFepxoDbWGBrCws4lec15sVrHgwjAVCKNWTnquwtuLGg26s8p3Xud5vbXA9slmhQ+iBjLfO4Ta/1DKNfIhuRsaZh5f945v87sQUYlDfgnrpAmNM4/6rUvO7TYitz9uIMovcFQFk7zdd75DSWkT+q3ANSG3pqwfbUhSy3Qgh6Z56Wo/f/ndblX0Kr1jAiw2us/2xHhTcX/29xyw/6eEFoq3e3wirlDLht78KQRl6vMfDulE+n+RdbGTSuSAgApfWa9ym7lZXW8OiUj9cYaFsQMnUY8Vbl9opt3U4M931sUJ7gYk3Dys1OXGstW+q5O00zPY3welz/OI310uWuHoPocFu13EPKrVEWMkTIaVws5BR4O83Pbgp7KvXX8b3mngdmT2oHAUB51nCfe0sSpzzl9Cm4tzS1V9sMopc2Vi/qs0s5h4mubQ0Yu993Qot2Wt65cwqbZsoWYCtXYg73twq/6JzODTrbIqRTXKPO6dx4s0C7V5oFV6yCnDqkHgBSGpRmyKbTuZw+9Xo7hfv0+Bqn17Qhel7hGGkUL8UDm1YNyjtMdKf1tSfsAdmg5Rq0XEt7QHS5ANqtKCdRZFuwQWPQfa84j7cIsZ5zG7b+QU/vAeiOXz/XeYXTFMH1YzakphcA1GersTxMtVaG1zk4tjL5/THZcO5BH5fTn+q8vdM/j3/rNJ9vRc/sXAaNQfflsMm1OT14yM0elHmt53MfdG43LvGYLShd6pZvO43t4B/UPq+waVN2zdr55WEvJrEehoeA1D96nbeBr9NS2qqs0Hx3aotT+LF6peUVnjentm0Vdty92uYVfs5L6ZWmDKwp9TMecyk15rOTgj/H1tMblVN7G6rT/DpJDwtL747HlvM9c7OAc6+8xzgl3es2m8j3WeuDyaWadP5LbgtmhcyS5yLZfpydAKB+vZZdHjPSKJ2t1jm8vPRUMWtDrW1Bsa2Wtf6CjfbptXxWNnyr9nnFKfmADoWV3oe71zIbeXZMnQCgHb2WWR5bUDLnjhP42O6QvtR6huvbfdKrvDUuKLbVMoLuQXFrGrXGHi60ft6c4tDDvWKlA27Ta1mFjs2t6gUA7ek1lmFLKY8tMCLYzmPQ2NMdshNJS2qr4639tNO6bDU+4Gm1nBo03iuD1mWrtoPu2OuNxdNWrIaA29iwrNafjg8aC9B3AoB2WRnWenl8GsLYCzkNGq+dJY6UOC2QVlsdf8rX2rYLswc7LZZTO61rNMhjW7X7sGFQnEFYrVoCbjNovAl/Unssz1aA7gQA7Rs0lmktzhG1hvhnYivGknqN52DQMuxUfx3fa/nbZz02aDwvrbQbrTxlO73xPvpa7bWZf1W4QcQIq1ZTwG0GjXOfW6k0Bo2FRicKUADLYmWaDcduZSsty6/18rU81HRJBo1Bd8tBoF1Hlv9WeuS2arfjIpSdo051X2enETdMbzkbNF6rLZUPNroltG5Z0z2JJ9QWcJ9sVXelcdmw2wkAlst6ii1wsjJvUJ22GvPYC7XZqr3A+1THW763asugMQC1vK+pkb/V2G6sbVSO5YcRN8/bqp3y4VQuTDWIugkB9grbf65XGKfw/XznTn8dj6OVlQZDj7NTW5zCj9UrLa/wvDm1bau8ZUUtvMLPee2cxvOz1/zla0i6V/g93Ee8bymt5PMlncbzVsP18zi1Vsffwmksi/fK+1l2KsepfLvxXtPKppx5q1mn/OXDvabpJ7z2Xu235fC05PfdPuBNLPWK41Sm0jjdjDYUqLVKOPR4O7XFKfxYvdLyCs+bU9u2KlNWlOYVfs5bYWVhd0i/a/7y9rVkQZEN7fOK00fkoZRW8nkLp/E87pX/Gnqcflb6uqAGXuNnfq/0n2mn8pzytxvvFXYtPWRMLXAaryG7N/dKf86m6l7J16meYiuw5Zp0nX2idgw6F+BvjukrpQtKBo3DsXZi2DgAXLKhddtj+kJj2fzV8ftU72dDMn87fmWOdvsGjQ+yLdl14w/pm+P3qRupa72edrpuz3iNbSj7zP+p8XN3x585tW/Qud3odS6nnOa107ig1laUTXMZdK5jjF2jTudr1b7/VNfXbE7bY/Ia45HPj/8/HNIf4lrAI3/TdPZEx2k6m/fQa36nivpUiIY0+OymeK/xJrGvNOgAYDqnc5n8ucKDp0FjI/ZUJu8EM7V3KqSOr8Gpce11blxbmnotWT0+HNOfOl9Lg7BmX1ykqeXUoPE6sutpd0y0F4H1mVQfLyHgforT609pLytiCksASOPUA/FST8SpPD59xdPWEnC/xOncs/WcQVxHmOal3tLh0VcAmFofTxY6l6IXAAAINbXeBQAA85tUH9e6LRgAAAAAAE0j4AYAAAAAIAECbgAAAAAAEiDgBgAAAAAgAQJuAAAAAAASIOAGAAAAACABAm4AAAAAABIg4AYAAAAAIAECbgAAAAAAEiDgBgAAAAAgAQJuAAAAAAASIOAGAAAAACABAm4AAAAAABIg4AYAAAAAIAECbgAAAAAAEiDgBgAAAAAgAQJuAAAAAAASIOAGAAAAACABAm4AAAAAABIg4AYAAAAAIAECbgAAAAAAEiDgBgAAAAAgAQJuAAAAAAASIOAGAAAAACABAm4AAAAAABIg4AYAAAAAIAECbgAAAAAAEiDgBgAAAAAgAQJuAAAAAAASIOAGAAAAACABAm4AAAAAABIg4AYAAAAAIAECbgAAlulTAQCAOU2uWwm4AQBow6BpnAAAwJy+0DQDATcAAG34oGm8AADAnAi4AQBYqD80zTcCAABzmlq3/kHADQBAG95rGi+GlQMAMBen6aPH6OEGAKARO013JwAAMIeQOnX3N03nFOaDps8/AwAAZ39p+gqpX2p67zgAADhzh7TXNMMhfSYAANCMd4f0MDFZA4EtwgAACGN1qNWlU+vfjQAAQFO8plf4VPoAAIT7WWF179QVzQEAQAXuFVbxW4OBnm4AAG5jdaY9sA6pc38XAABokldY5X8aXu4EAABeYr3TVmeG1redAABAs+4V3gg4DTF3AgAAl5zCe7UvH24DAICGecU1Bk7p/pDeHl+P4eYAgLWxus96s60utDpxjrrVXb5ByLZgAACgPFux/AcBAIBa/Edj8P4/CLgBAGiTPZW3RVmcAABAacMhfXlIHy7/k4AbAIB2OY1BN8PBAQAox4JsC7aHxz8g4AYAoG0294ztRwAAKMeC7fdP/eDvAgAALbMK/nsBAIASrA5+/9wP6eEGAGAZrKfbVlhleDkAAOnZMPKv9UKwbQi4AQBYDqcx6HYCAACpDBqD7eG1X2RIOQAAyzFonEf2HwEAgBSsjn1ygbSn0MMNAMAyOdHbDQDAXHaH9O/j15vRww0AwDINh/SZXlnMBQAAvGincfj415oYbBt6uAEAWAdbVO3tIX0ler0BAHiJLYj20yH9ooAg+xIBNwAA62PBt9cYeH9+/OoEAMD6DBoDbBsN9ofGAHu2kWH/H3OcNjlnM1R3AAAAAElFTkSuQmCC
  </div>

  <div class="top-header">
    <img id="logoImage" class="logo-image" alt="Company Logo">
    <span class="company-name"></span>
  </div>

  <div class="receipt-container">
    <div class="container-header">
      <div class="header">
        <h2>Receipt from Primastat</h2>
        <div class="amount">{{currency}} {{total_amount}}</div>
        <div class="date">{{date_of_payment}}</div>
      </div>
      <svg class="receipt-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 7.8C4 6.11984 4 5.27976 4.32698 4.63803C4.6146 4.07354 5.07354 3.6146 5.63803 3.32698C6.27976 3 7.11984 3 8.8 3H15.2C16.8802 3 17.7202 3 18.362 3.32698C18.9265 3.6146 19.3854 4.07354 19.673 4.63803C20 5.27976 20 6.11984 20 7.8V21L12 17L4 21V7.8Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <div class="download-section">
        <div class="separator"></div>
        <div class="download-buttons">
          <a href="#" class="download-button">
            <span class="download-arrow" aria-hidden="true"></span>
            Download invoice
          </a>
          <a href="#" class="download-button">
            <span class="download-arrow" aria-hidden="true"></span>
            Download receipt
          </a>
        </div>
    </div>

    <div class="details">
      <div class="detail-label">Receipt number</div>
      <div class="detail-value">{{receipt_number}}</div>
      
      <div class="detail-label">Invoice number</div>
      <div class="detail-value">{{invoice_number}}</div>
      
      <div class="detail-label">Payment method</div>
      <div class="detail-value">href="https://www.razorpay.com/docs/payment-gateway/payments/international-payments/">Credit card</a></div>
    </div>
  </div>

  <div class="details-container">
    <h3 class="details-header">Receipt #{{receipt_number}}</h3>
    <div class="details-date">{{payment_period}}</div>
    
    <div class="item">
      <div>
        <div>{{product}}</div>
        <div class="item-details">Qty {{product_quantity}}</div>
      </div>
      <div class="amount-cell">{{currency}}{{product_cost}}</div>
    </div>
    
    <div class="total">
      <div>Total</div>
      <div>{{currency}}{{total_amount}}</div>
    </div>
    
    <div class="total">
      <div>Amount paid</div>
      <div>{{currency}}{{amount_payed}}</div>
    </div>
  </div>

  <script>
    // Wait for the DOM to be fully loaded before running our code
    document.addEventListener('DOMContentLoaded', function() {
      // Get the base64 data from the hidden element
      const base64Data = document.getElementById('imageData').textContent.trim();
      
      // Function to decode and load the image
      function loadImage(base64String) {
        try {
          // Get the image element
          const imgElement = document.getElementById('logoImage');
          
          // Set up load event handler
          imgElement.onload = function() {
            // Add the 'loaded' class to fade in the image
            imgElement.classList.add('loaded');
            console.log('Image loaded successfully');
          };
          
          // Set the image source to our base64 data
          imgElement.src = base64String;
        } catch (error) {
          console.error('Error loading image:', error); 
        }
      }

      // Load the image when the page is ready
      if (base64Data) {
        loadImage(base64Data);
      } else {
        console.error('No image data found');
      }
    });
  </script>
</body>
</html>



"""


async def send_email(email_data):
    try:
        template = Template(html_template)
        render_html = template.render(email_data)
        print(render_html)
        response = ses_client.send_email(
            Source='neevdeb26@gmail.com',
            Destination={'ToAddresses': [email_data['email-id']]},
            Message={'Subject': {'Data': 'Test Email'}, 'Body': {'Html': {'Data': render_html}}}
        )
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"message": str(e)}


app = FastAPI()

@app.post("/due-payments")
async def get_due_payments():
    response = await requests.get('razorpay_url')

    response_json = response.json()




    data = response_json['data']

    if len(data) == 0:
        raise HTTPException(status_code=404, detail="No due payments found")
    else:
        # filter the payment list where message is 'Paid'
        data = [payment for payment in data if payment['status'] == 'Paid']
        
        for payment in data:
            
            invoice_data ={
  "customerName": payment['customer_name'],
  "currency": payment['currency'],
  "totalAmount": payment['amount per reccurence'],
  "amountPayed": payment['amount per reccurence'],
  "invoice_number": payment['invoice_number'],
  "payemntPeriod": str(payment['duration_from'] ) + " to " + payment['duration_upto'],
  "product": payment['product'],
  "productCost": payment['amount per reccurence'],
  "productQuantity": "1",
  "paymentDate": payment["due_date"],
  "email": payment['customer_email']

}
            headers = {
  'Content-Type': 'application/json'
}
            response = requests.post(invoice_creation_url, headers=headers, data=json.dumps(invoice_data))
            response_json = response.json()
            location = response_json['location']


            email_data = {
        "total_amount": payment['amount per reccurence'],
        "date_of_payment": payment["due_date"],
        "invoice_number": payment['invoice_number'],
        "payment_period":  str(payment['duration_from'] ) + " to " + payment['duration_upto'],
        "product": payment['product'],
        "product_quantity": "1",
        "product_cost": payment['amount per reccurence'],
        "amount_payed": payment['amount per reccurence'],
        "currency": payment['currency'],
        "email-id": payment['customer_email'],
        

    }
            
            response = await send_email(email_data)

    return {"message": "Email sent successfully"}



def lambda_handler(event, context):
    response = app(event, context)
    return response


 

