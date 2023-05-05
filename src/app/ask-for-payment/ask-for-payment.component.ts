import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {Merchant} from "../payment/payment.component";
import {showMessage} from "../../tools";
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";


export function _ask_for_paiement(vm:any,token_id:string,to_paid:number,to_paid_in_fiat:number,
                                  merchant:Merchant,
                                  provider:any=null,
                                  title="Paiement",
                                  subtitle="",
                                  intro_payment="Coût de l'opération",
                                  billing_address="",
                                  bill_content:{description:string,subject:string,contact:string},
                                  buy_method="")  {
    return new Promise((resolve, reject) => {
        vm.dialog.open(AskForPaymentComponent,{
            width: '450px',height:"auto",
            data:
                {
                    to_paid:to_paid,
                    to_paid_in_fiat:to_paid_in_fiat,
                    title: title,
                    billing_to:billing_address,
                    buy_method:buy_method,
                    subtitle:subtitle,
                    provider:provider,
                    intro_payment:intro_payment,
                    merchant:merchant,
                    bill:bill_content
                }
        }).afterClosed().subscribe((resp:any) => {
            if(resp) {
                resolve(resp);
            } else {
                resolve(null)
            }
        },(err:any)=>{reject(err)});
    });
}


@Component({
    selector: 'app-ask-for-payment',
    templateUrl: './ask-for-payment.component.html',
    styleUrls: ['./ask-for-payment.component.css']
})
export class AskForPaymentComponent implements OnInit {

    buy_method: "fiat" | "crypto" | "" = "";

    constructor(public dialogRef: MatDialogRef<AskForPaymentComponent>,
                public user:UserService,
                public network:NetworkService,
                @Inject(MAT_DIALOG_DATA) public data: any) { }

    ngOnInit(): void {
        this.buy_method=this.data.buy_method;
        if(this.data.merchant.currency=="")this.buy_method="crypto";
        if(!this.data.merchant.wallet)this.buy_method="fiat";
    }

    onpaid($event: any) {
        if($event){
            let rc:any=$event;
            rc.data=this.data
            rc.buy_method=this.buy_method;
            let amount="Réglement de "+rc.data.price+" "+rc.unity;
            if(rc.billing_to!=""){
                this.network.send_bill(rc.billing_to,
                    amount,
                    this.data.bill.subject,
                    rc["transaction"],
                    this.data.bill.message || "La transaction est consultable directement sur la blockchain",
                    this.data.bill.description
                ).subscribe(()=>{
                    showMessage(this,"Votre facture a été envoyé");
                    this.dialogRef.close(rc);
                })
            } else {
                showMessage(this,"Paiement enregistré");
                this.dialogRef.close(rc);
            }
        }
    }

    set_payment_in_crypto() {
        this.buy_method='crypto';
    }

    cancel() {
        this.buy_method="";
        this.dialogRef.close();
    }

    init_provider($event:any) {
        this.data.provider=$event.provider;
        this.data.addr=$event.address
        this.user.init($event.address,this.data.wallet.network,false,true,this.user.profil.email)
    }
}
