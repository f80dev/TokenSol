import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SvgComponent } from './svg.component';
import {HttpClientModule} from "@angular/common/http";

describe('SvgComponent', () => {
  let component: SvgComponent;
  let fixture: ComponentFixture<SvgComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SvgComponent ],
      imports: [HttpClientModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SvgComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
