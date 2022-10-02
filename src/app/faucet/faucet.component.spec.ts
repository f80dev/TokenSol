import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FaucetComponent } from './faucet.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('FaucetComponent', () => {
  let component: FaucetComponent;
  let fixture: ComponentFixture<FaucetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FaucetComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FaucetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
