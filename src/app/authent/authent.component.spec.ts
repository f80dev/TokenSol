import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthentComponent } from './authent.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {GoogleLoginProvider, SocialAuthService, SocialAuthServiceConfig} from "angularx-social-login";
import {GOOGLE_CLIENT_ID} from "../../definitions";

describe('AuthentComponent', () => {
  let component: AuthentComponent;
  let fixture: ComponentFixture<AuthentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AuthentComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule],
      providers:[
        {provide:SocialAuthService,
          useValue: {
            autoLogin: false,
            providers: [
              {
                id: GoogleLoginProvider.PROVIDER_ID,
                provider: new GoogleLoginProvider(GOOGLE_CLIENT_ID),
              }
            ],
          } as SocialAuthServiceConfig}
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
