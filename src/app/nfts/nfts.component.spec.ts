import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NftsComponent } from './nfts.component';
import {HttpClientModule} from "@angular/common/http";
import {MatDialogModule} from "@angular/material/dialog";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('NftsComponent', () => {
  let component: NftsComponent;
  let fixture: ComponentFixture<NftsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NftsComponent ],
      imports: [HttpClientModule,MatDialogModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NftsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
