import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {Merchant} from "../payment/payment.component";
import {$$, Bank, showMessage} from "../../tools";
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {Connexion} from "../../operation";

export function _ask_for_paiement(vm:any,
                                  token_id:string,
                                  to_paid:number,
                                  to_paid_in_fiat:number,
                                  merchant:Merchant,
                                  provider:any=null,
                                  title="Paiement",
                                  subtitle="",
                                  intro_payment="Coût de l'opération",
                                  billing_address="",
                                  bill_content:{description:string,subject:string,contact:string}= {description: '', subject: '', contact: ''},
                                  buy_method="",
                                  bank:Bank | undefined=undefined)  {
    //token_id : reference du token utilisable pour le paiement
    return new Promise((resolve, reject) => {
        if(to_paid==0 && to_paid_in_fiat==0){
            resolve({})
        }else{
            if(!vm.dialog){$$("!La fenetre n'integre pas MatDialog") }
            vm.dialog.open(AskForPaymentComponent,{
                width: '450px',height:"auto",
                data:
                    {
                        to_paid:to_paid,
                        to_paid_in_fiat:to_paid_in_fiat,
                        title: title,
                        bank:bank,
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
        }
    });
}


@Component({
    selector: 'app-ask-for-payment',
    templateUrl: './ask-for-payment.component.html',
    styleUrls: ['./ask-for-payment.component.css']
})
export class AskForPaymentComponent implements OnInit {

    buy_method: "fiat" | "crypto" | "" = "";
    nb_payment=0;
    connexion: Connexion = {
        private_key: false,
        address: false,
        direct_connect: true,
        email: false,
        extension_wallet: true,
        google: false,
        keystore: false,
        nfluent_wallet_connect: false,
        on_device: false,
        wallet_connect: true,
        web_wallet: true,
        webcam: false
    };


    constructor(public dialogRef: MatDialogRef<AskForPaymentComponent>,
                public user:UserService,
                public network:NetworkService,
                @Inject(MAT_DIALOG_DATA) public data: any) { }

    ngOnInit(): void {
        this.buy_method=this.data.buy_method;
        if(!this.data.merchant || (!this.data.merchant.currency && (!this.data.merchant.wallet && !this.data.merchant.wallet.token))){
            this.dialogRef.close(true)
        }

        if(this.data.merchant!.wallet!.token)this.nb_payment=this.nb_payment+1;
        if(this.data.merchant!.id)this.nb_payment=this.nb_payment+1;
        if(this.data.connexion)this.connexion=this.data.connexion

        if(this.data.merchant.currency=="")this.buy_method="crypto";
        if(!this.data.merchant.wallet)this.buy_method="fiat";

        if(Number(this.data.to_paid)==0 && Number(this.data.to_paid_in_fiat)==0){
            this.dialogRef.close({})
        }
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
        this.data.url_direct_xportal_connect=$event.url_direct_xportal_connect
        if(this.data.merchant.wallet){
            this.user.init($event.address,this.data.merchant.wallet.network,false,true,this.user.profil.email)
        }
    }
}
